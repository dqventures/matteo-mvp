"""
Metrica Logistics Intelligence — Synthetic Data Generator

Generates 50,000 realistic UK parcel shipment records for testing the
KPI engine and report pipeline. The data has deliberate performance
differences between Carrier A and Carrier B so the report surfaces
genuine trade-offs.

Usage:
    python scripts/generate_synthetic_data.py

Output:
    output/synthetic_shipments.csv
"""

import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOTAL_SHIPMENTS = 50_000
PERIOD_START = datetime(2025, 1, 1)
PERIOD_END = datetime(2025, 12, 31)
RANDOM_SEED = 42  # reproducible runs

# Peak trading window
PEAK_START = datetime(2025, 11, 15)
PEAK_END = datetime(2025, 12, 23)

# Carrier / service distribution
# 60% Carrier A, 40% Carrier B
# Within each carrier: 30% Next Day, 70% Standard
CARRIER_SERVICE_WEIGHTS = [
    ("Carrier A", "Next Day", 0.60 * 0.30),   # 18%
    ("Carrier A", "Standard", 0.60 * 0.70),   # 42%
    ("Carrier B", "Next Day", 0.40 * 0.30),   # 12%
    ("Carrier B", "Standard", 0.40 * 0.70),   # 28%
]

# Shipment status distribution
STATUS_WEIGHTS = [
    ("Delivered", 0.95),
    ("Failed", 0.02),
    ("Returned", 0.02),
    ("Lost", 0.01),
]

# Late-shipment severity (days late, among late shipments)
LATE_SEVERITY = [
    (1, 0.50),
    (2, 0.30),
    (3, 0.10),
    (4, 0.05),
    (5, 0.05),
]

# ---------------------------------------------------------------------------
# UK Postcode areas with population-based weights
# ---------------------------------------------------------------------------

# London postcodes (~25% of total)
LONDON_AREAS = ["EC", "WC", "E", "N", "NW", "W", "SW", "SE"]

# Major city postcodes (~30% of total)
MAJOR_CITY_AREAS = ["M", "B", "L", "LS", "S", "NE", "BS", "CF", "EH", "G"]

# Other postcodes (~45% of total)
OTHER_AREAS = [
    "BA", "OX", "CB", "EX", "PL", "IP", "PE", "NG", "DE", "ST",
    "WR", "HR", "SN", "GL", "CT", "ME", "TN", "RH", "GU", "PO",
    "SO", "BH", "DT", "TA", "TR", "AB", "DD", "FK", "KY", "PA",
    "IV", "PH", "LL", "SA", "SY", "LD", "NP",
]

# Rural Scotland / Wales postcodes (subset of OTHER — used for performance curves)
RURAL_AREAS = {"AB", "DD", "FK", "KY", "PA", "IV", "PH", "LL", "SA", "SY", "LD"}

def build_postcode_pool():
    """Return a list of (area, weight) tuples that sum to 1.0."""
    pool = []
    london_w = 0.25 / len(LONDON_AREAS)
    for a in LONDON_AREAS:
        pool.append((a, london_w))
    city_w = 0.30 / len(MAJOR_CITY_AREAS)
    for a in MAJOR_CITY_AREAS:
        pool.append((a, city_w))
    other_w = 0.45 / len(OTHER_AREAS)
    for a in OTHER_AREAS:
        pool.append((a, other_w))
    return pool

# ---------------------------------------------------------------------------
# Baseline on-time rates per carrier+service
# ---------------------------------------------------------------------------

BASELINE_OTD = {
    ("Carrier A", "Next Day"): 0.92,
    ("Carrier A", "Standard"): 0.88,
    ("Carrier B", "Next Day"): 0.88,
    ("Carrier B", "Standard"): 0.90,
}

# Weekly std-dev of on-time rate (used to jitter per-week performance)
WEEKLY_STD = {
    "Carrier A": 0.025,   # 2.5 pp
    "Carrier B": 0.06,    # 6 pp
}

# Peak degradation (subtracted from OTD during peak window)
PEAK_DEGRADATION = {
    "Carrier A": 0.065,   # ~6.5 pp drop
    "Carrier B": 0.125,   # ~12.5 pp drop
}

# Regional adjustments — delta applied on top of baseline
REGIONAL_DELTA = {
    # Carrier A: good in urban, weak in rural Scotland/Wales
    ("Carrier A", "urban"):  +0.02,
    ("Carrier A", "rural"):  -0.06,
    ("Carrier A", "other"):   0.00,
    # Carrier B: weak in London, strong in rural
    ("Carrier B", "urban"):  -0.03,
    ("Carrier B", "rural"):  +0.03,
    ("Carrier B", "other"):   0.00,
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_promises(path="scripts/config/carrier_promises.json"):
    with open(path) as f:
        data = json.load(f)
    lookup = {}
    for p in data["promises"]:
        key = (p["carrier_name"], p["service_name"])
        lookup[key] = p
    return lookup

def region_type(postcode_area):
    """Classify a postcode area as urban (London), rural, or other."""
    if postcode_area in LONDON_AREAS:
        return "urban"
    if postcode_area in RURAL_AREAS:
        return "rural"
    return "other"

def weighted_choice(items_weights, rng):
    """Pick from [(item, weight), ...] using the given RNG."""
    items, weights = zip(*items_weights)
    return rng.choices(items, weights=weights, k=1)[0]

def random_dispatch_time(date, rng):
    """Return a datetime on `date` with a random dispatch hour (08-18)."""
    hour = rng.randint(8, 17)
    minute = rng.randint(0, 59)
    return datetime(date.year, date.month, date.day, hour, minute, 0)

def add_working_days(start, days, working_day_names):
    """Add `days` working days to `start`, returning the target date."""
    working_day_indices = set()
    day_name_to_idx = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    for name in working_day_names:
        working_day_indices.add(day_name_to_idx[name])

    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() in working_day_indices:
            added += 1
    return current

def delivery_datetime(promised_date, rng):
    """Generate a delivery time on the promised date (between 07:00 and 20:00)."""
    hour = rng.randint(7, 19)
    minute = rng.randint(0, 59)
    return datetime(promised_date.year, promised_date.month, promised_date.day, hour, minute, 0)

def generate_dispatch_dates(rng):
    """Generate all dispatch dates (Mon-Fri) with a slight Monday spike."""
    dates = []
    current = PERIOD_START
    while current <= PERIOD_END:
        weekday = current.weekday()
        if weekday < 5:  # Mon-Fri
            dates.append(current)
        current += timedelta(days=1)
    return dates

# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate():
    rng = random.Random(RANDOM_SEED)
    promises = load_promises()
    postcode_pool = build_postcode_pool()

    # Pre-generate dispatch dates
    dispatch_dates = generate_dispatch_dates(rng)

    # Build day-of-week weights (Monday spike)
    dow_weights = {0: 1.3, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.9}  # Mon=0 ... Fri=4

    # Pre-compute per-week OTD jitter for each carrier
    # ISO weeks 1–52 for 2025
    weekly_jitter = {}
    for carrier in ["Carrier A", "Carrier B"]:
        std = WEEKLY_STD[carrier]
        weekly_jitter[carrier] = {w: rng.gauss(0, std) for w in range(1, 54)}

    # Carrier+service selection weights
    cs_items = [(cs[:2], cs[2]) for cs in CARRIER_SERVICE_WEIGHTS]

    # Status selection weights
    status_items = STATUS_WEIGHTS

    rows = []
    for _ in range(TOTAL_SHIPMENTS):
        # 1. Pick carrier + service
        carrier, service = weighted_choice(cs_items, rng)

        # 2. Pick dispatch date (weighted by day of week)
        date = rng.choice(dispatch_dates)
        # Apply day-of-week weighting via accept/reject
        while rng.random() > dow_weights[date.weekday()] / 1.3:
            date = rng.choice(dispatch_dates)

        ship_dt = random_dispatch_time(date, rng)

        # 3. Pick destination postcode
        area = weighted_choice(postcode_pool, rng)
        district_num = rng.randint(1, 9)
        postcode = f"{area}{district_num}"

        # 4. Calculate promised delivery date
        promise = promises[(carrier, service)]
        promised_date = add_working_days(
            ship_dt, promise["promised_transit_days"], promise["working_days"]
        )
        promised_dt = datetime(
            promised_date.year, promised_date.month, promised_date.day, 23, 59, 0
        )

        # 5. Pick shipment status
        status = weighted_choice(status_items, rng)

        # 6. Calculate actual delivery (only for "Delivered")
        delivered_dt = None
        if status == "Delivered":
            # Determine effective on-time probability for this shipment
            base_otd = BASELINE_OTD[(carrier, service)]
            iso_week = ship_dt.isocalendar()[1]
            jitter = weekly_jitter[carrier].get(iso_week, 0)

            # Regional adjustment
            reg = region_type(area)
            reg_delta = REGIONAL_DELTA.get((carrier, reg), 0)

            # Peak adjustment
            is_peak = PEAK_START <= ship_dt <= PEAK_END
            peak_delta = -PEAK_DEGRADATION[carrier] if is_peak else 0

            effective_otd = max(0.40, min(0.99, base_otd + jitter + reg_delta + peak_delta))

            if rng.random() < effective_otd:
                # On time — deliver on or before promised date
                # Most on-time deliveries arrive on the promised day
                days_early = rng.choices([0, 0, 0, 0, 1], k=1)[0]  # 80% same day, 20% 1 day early
                actual_date = promised_date - timedelta(days=days_early)
                delivered_dt = delivery_datetime(actual_date, rng)
            else:
                # Late — pick severity
                delay = weighted_choice(LATE_SEVERITY, rng)
                actual_date = promised_date + timedelta(days=delay)
                delivered_dt = delivery_datetime(actual_date, rng)

        rows.append({
            "Shipment_ID": str(uuid.UUID(int=rng.getrandbits(128))),
            "Carrier": carrier,
            "Service_Type": service,
            "Ship_DateTime": ship_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Delivered_DateTime": delivered_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if delivered_dt else "",
            "Promised_Delivery_DateTime": promised_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Shipment_Status": status,
            "Destination_Postcode": postcode,
        })

    return rows

def main():
    print("Generating 50,000 synthetic shipment records...")
    rows = generate()

    output_path = Path("output/synthetic_shipments.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Shipment_ID", "Carrier", "Service_Type", "Ship_DateTime",
        "Delivered_DateTime", "Promised_Delivery_DateTime",
        "Shipment_Status", "Destination_Postcode",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Print summary stats
    total = len(rows)
    carriers = {}
    statuses = {}
    for r in rows:
        c = r["Carrier"]
        s = r["Shipment_Status"]
        carriers[c] = carriers.get(c, 0) + 1
        statuses[s] = statuses.get(s, 0) + 1

    print(f"\nDone! Wrote {total:,} rows to {output_path}")
    print(f"\nCarrier split:")
    for c, n in sorted(carriers.items()):
        print(f"  {c}: {n:,} ({n/total*100:.1f}%)")
    print(f"\nStatus split:")
    for s, n in sorted(statuses.items()):
        print(f"  {s}: {n:,} ({n/total*100:.1f}%)")

if __name__ == "__main__":
    main()

"""
Metrica Logistics Intelligence — Data Validator

Checks that a shipment CSV file is ready for report generation.
Runs a series of validation checks and prints a pass/fail report.

Usage:
    python scripts/validate_data.py output/synthetic_shipments.csv \
        --config scripts/config/report_request.json \
        --promises scripts/config/carrier_promises.json
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd


def load_config(path):
    with open(path) as f:
        return json.load(f)


def parse_date(s):
    """Try to parse an ISO 8601 datetime string."""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def run_validation(csv_path, config, promises):
    """Run all validation checks. Returns (passed: bool, report_lines: list)."""
    results = []
    all_passed = True

    # Load CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"ERROR: Could not read CSV file: {e}")
        sys.exit(1)

    total_rows = len(df)
    results.append(f"File: {csv_path}")
    results.append(f"Rows: {total_rows:,}")
    results.append("")

    # --- Check 1: Required columns ---
    required_cols = [
        "Shipment_ID", "Carrier", "Service_Type", "Ship_DateTime",
        "Delivered_DateTime", "Shipment_Status", "Destination_Postcode",
    ]
    # Promised_Delivery_DateTime is expected but not strictly required
    # (the KPI engine can compute it from config)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        results.append(f"[FAIL] Required columns missing: {', '.join(missing)}")
        all_passed = False
    else:
        results.append("[PASS] Required columns present")

    # --- Check 2: Date parsing ---
    date_cols = ["Ship_DateTime", "Delivered_DateTime"]
    date_issues = []
    for col in date_cols:
        if col not in df.columns:
            continue
        non_null = df[col].dropna().replace("", pd.NA).dropna()
        parsed = non_null.apply(lambda x: parse_date(str(x)))
        bad_count = parsed.isna().sum()
        if bad_count > 0:
            date_issues.append(f"{col}: {bad_count} unparseable values")

    if date_issues:
        results.append(f"[FAIL] Date parsing issues: {'; '.join(date_issues)}")
        all_passed = False
    else:
        results.append("[PASS] All dates parseable")

    # --- Check 3: No duplicate Shipment_IDs ---
    dup_count = df["Shipment_ID"].duplicated().sum()
    if dup_count > 0:
        results.append(f"[FAIL] {dup_count:,} duplicate Shipment_IDs found")
        all_passed = False
    else:
        results.append("[PASS] No duplicate Shipment_IDs")

    # --- Check 4: Carrier names match config ---
    promise_list = promises.get("promises", [])
    valid_carriers = set(p["carrier_name"] for p in promise_list)
    csv_carriers = set(df["Carrier"].unique())
    unknown_carriers = csv_carriers - valid_carriers
    if unknown_carriers:
        results.append(f"[FAIL] Unknown carriers: {', '.join(unknown_carriers)}")
        all_passed = False
    else:
        results.append("[PASS] All carriers match config")

    # --- Check 5: Service names match config ---
    valid_services = set(p["service_name"] for p in promise_list)
    csv_services = set(df["Service_Type"].unique())
    unknown_services = csv_services - valid_services
    if unknown_services:
        results.append(f"[FAIL] Unknown services: {', '.join(unknown_services)}")
        all_passed = False
    else:
        results.append("[PASS] All services match config")

    # --- Check 6: Time period coverage ---
    period_start = datetime.fromisoformat(config["period_start"]).date()
    period_end = datetime.fromisoformat(config["period_end"]).date()
    ship_dates = pd.to_datetime(df["Ship_DateTime"], utc=True)
    data_start = ship_dates.min().date()
    data_end = ship_dates.max().date()

    if data_start > period_start or data_end < period_end:
        results.append(
            f"[FAIL] Time period: data spans {data_start} to {data_end}, "
            f"but config requires {period_start} to {period_end}"
        )
        all_passed = False
    else:
        results.append(
            f"[PASS] Time period: {data_start} to {data_end} "
            f"(covers requested range)"
        )

    # --- Check 7: Geography coverage ---
    postcode_areas = df["Destination_Postcode"].str.extract(r"^([A-Za-z]+)")[0].nunique()
    if postcode_areas == 0:
        results.append("[FAIL] Geography: no valid postcode areas found")
        all_passed = False
    else:
        results.append(f"[PASS] Geography: {postcode_areas} postcode areas found")

    # --- Check 8: Sample size per carrier+service ---
    threshold = config.get("data_sufficiency_threshold", 30)
    # Calculate weeks in the period
    total_weeks = max(1, ((period_end - period_start).days) / 7)

    cs_counts = df.groupby(["Carrier", "Service_Type"]).size()
    min_per_week = None
    min_label = ""
    for (carrier, service), count in cs_counts.items():
        per_week = count / total_weeks
        if min_per_week is None or per_week < min_per_week:
            min_per_week = per_week
            min_label = f"{carrier} / {service}"

    if min_per_week is not None and min_per_week < threshold:
        results.append(
            f"[FAIL] Sample size: {min_label} has only {min_per_week:.0f} "
            f"shipments/week (threshold: {threshold})"
        )
        all_passed = False
    else:
        results.append(
            f"[PASS] Sample size: minimum {min_per_week:.0f} shipments/week "
            f"per carrier/service"
        )

    # --- Check 9: Missing data ---
    # Check Delivered_DateTime null for "Delivered" status
    delivered_rows = df[df["Shipment_Status"] == "Delivered"]
    # Treat empty strings as null
    null_delivered_dt = delivered_rows["Delivered_DateTime"].replace("", pd.NA).isna().sum()
    if null_delivered_dt > 0:
        results.append(
            f"[FAIL] Missing data: Delivered_DateTime null for "
            f"{null_delivered_dt:,} \"Delivered\" rows"
        )
        all_passed = False
    else:
        results.append(
            f"[PASS] Missing data: Delivered_DateTime null for 0 \"Delivered\" rows"
        )

    # --- Check 10: Shipment status values ---
    status_counts = Counter(df["Shipment_Status"])
    status_parts = [f"{s} ({c:,})" for s, c in sorted(status_counts.items())]
    results.append(f"[INFO] Shipment statuses found: {', '.join(status_parts)}")

    return all_passed, results


def main():
    parser = argparse.ArgumentParser(description="Validate shipment data for Metrica reports")
    parser.add_argument("csv_path", help="Path to the shipment CSV file")
    parser.add_argument("--config", required=True, help="Path to report_request.json")
    parser.add_argument("--promises", required=True, help="Path to carrier_promises.json")
    args = parser.parse_args()

    config = load_config(args.config)
    promises = load_config(args.promises)

    print("\n=== DATA VALIDATION REPORT ===")
    passed, lines = run_validation(args.csv_path, config, promises)
    for line in lines:
        print(line)

    print()
    if passed:
        print("RESULT: PASS — data is ready for report generation")
        sys.exit(0)
    else:
        print("RESULT: FAIL — fix the issues listed above")
        sys.exit(1)


if __name__ == "__main__":
    main()

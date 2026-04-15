"""
Metrica Logistics Intelligence — Report Computation Orchestrator

Loads shipment data and config, runs the KPI engine, and writes
the full kpis.json output file.

Usage:
    python scripts/compute_report.py \
        --data output/synthetic_shipments.csv \
        --config scripts/config/report_request.json \
        --promises scripts/config/carrier_promises.json \
        --output output/kpis.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from kpi_engine import (
    compute_on_time_performance,
    compute_weekly_consistency,
    compute_volatility,
    compute_severity_distribution,
    compute_regional_performance,
    compute_peak_delta,
    compute_trade_offs,
)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_promise_lookup(promises_config):
    """Build a lookup dict: (carrier, service) -> promise record."""
    lookup = {}
    for p in promises_config["promises"]:
        key = (p["carrier_name"], p["service_name"])
        lookup[key] = p
    return lookup


def preprocess(df, config, promises_lookup):
    """
    Apply all pre-processing steps from the spec:
    1. Filter to Delivered only
    2. Filter to report time period
    3. Filter to carriers/services in scope
    4. Derive postcode_area
    5. Calculate on_time_flag
    6. Calculate delay_days
    7. Assign week_number
    8. Assign peak_flag
    """
    # Parse dates
    df["Ship_DateTime"] = pd.to_datetime(df["Ship_DateTime"], utc=True)
    df["Delivered_DateTime"] = pd.to_datetime(df["Delivered_DateTime"], utc=True, errors="coerce")
    df["Promised_Delivery_DateTime"] = pd.to_datetime(df["Promised_Delivery_DateTime"], utc=True, errors="coerce")

    # 1. Filter to delivered
    df = df[df["Shipment_Status"] == "Delivered"].copy()
    print(f"  After filtering to Delivered: {len(df):,} rows")

    # 2. Filter to report time period
    period_start = pd.Timestamp(config["period_start"], tz="UTC")
    period_end = pd.Timestamp(config["period_end"], tz="UTC") + pd.Timedelta(days=1)  # inclusive
    df = df[(df["Ship_DateTime"] >= period_start) & (df["Ship_DateTime"] < period_end)]
    print(f"  After filtering to period: {len(df):,} rows")

    # 3. Filter to carriers and services in scope
    df = df[df["Carrier"].isin(config["carriers_in_scope"])]
    df = df[df["Service_Type"].isin(config["services_in_scope"])]
    print(f"  After filtering carriers/services: {len(df):,} rows")

    # 4. Derive postcode_area (first alpha characters)
    df["postcode_area"] = df["Destination_Postcode"].str.extract(r"^([A-Za-z]+)")[0].str.upper()

    # 5. Deduplicate on Shipment_ID (keep first)
    before = len(df)
    df = df.drop_duplicates(subset="Shipment_ID", keep="first")
    if len(df) < before:
        print(f"  Removed {before - len(df)} duplicates")

    # 6. Calculate on_time_flag
    df["on_time_flag"] = df["Delivered_DateTime"] <= df["Promised_Delivery_DateTime"]

    # 7. Calculate delay_days (calendar days late, 0 if on-time)
    df["delay_days"] = (
        (df["Delivered_DateTime"] - df["Promised_Delivery_DateTime"])
        .dt.total_seconds() / 86400
    ).clip(lower=0).round().astype(int)

    # 8. Assign week_number (ISO week)
    df["week_number"] = df["Ship_DateTime"].dt.isocalendar().week.astype(int)

    # 9. Assign peak_flag
    peak_start = pd.Timestamp(config["peak_start"], tz="UTC")
    peak_end = pd.Timestamp(config["peak_end"], tz="UTC") + pd.Timedelta(days=1)
    df["peak_flag"] = (df["Ship_DateTime"] >= peak_start) & (df["Ship_DateTime"] < peak_end)

    return df


def main():
    parser = argparse.ArgumentParser(description="Compute Metrica KPIs from shipment data")
    parser.add_argument("--data", required=True, help="Path to shipment CSV")
    parser.add_argument("--config", required=True, help="Path to report_request.json")
    parser.add_argument("--promises", required=True, help="Path to carrier_promises.json")
    parser.add_argument("--output", required=True, help="Path to write kpis.json")
    args = parser.parse_args()

    # Load inputs
    print("Loading data and config...")
    df = pd.read_csv(args.data)
    config = load_json(args.config)
    promises = load_json(args.promises)
    promises_lookup = build_promise_lookup(promises)

    print(f"Raw data: {len(df):,} rows")

    # Pre-process
    print("\nPre-processing...")
    df = preprocess(df, config, promises_lookup)

    sufficiency_threshold = config.get("data_sufficiency_threshold", 30)

    # Compute KPIs
    print("\nComputing KPIs...")

    print("  1/6 On-Time Performance...")
    on_time = compute_on_time_performance(df)

    print("  2/6 Weekly Consistency...")
    consistency = compute_weekly_consistency(df)

    print("  3/6 Volatility...")
    volatility = compute_volatility(df)

    print("  4/6 Severity Distribution...")
    severity = compute_severity_distribution(df)

    print("  5/6 Regional Performance...")
    regional = compute_regional_performance(df, sufficiency_threshold)

    print("  6/6 Peak Delta...")
    peak = compute_peak_delta(df)

    print("\nComputing trade-offs...")
    trade_offs = compute_trade_offs(on_time, consistency, volatility, regional, peak)

    # Build output
    output = {
        "metadata": {
            "report_title": config["report_title"],
            "customer_name": config["customer_name"],
            "period_start": config["period_start"],
            "period_end": config["period_end"],
            "geography": config["geography_scope"],
            "carriers": config["carriers_in_scope"],
            "services": config["services_in_scope"],
            "intent": config["intent"],
            "peak_window": f"{config['peak_start']} to {config['peak_end']}",
            "total_shipments_analysed": len(df),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "on_time_performance": on_time,
        "weekly_consistency": consistency,
        "volatility": volatility,
        "severity_distribution": severity,
        "regional_performance": regional,
        "peak_delta": peak,
        "trade_offs": trade_offs,
    }

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone! KPIs written to {output_path}")

    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total shipments analysed: {len(df):,}")
    for carrier, stats in on_time["overall_otd"].items():
        print(f"  {carrier}: {stats['otd_pct']}% OTD ({stats['total_shipments']:,} shipments)")
    print(f"\nTrade-offs:")
    for key, val in trade_offs.items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    main()

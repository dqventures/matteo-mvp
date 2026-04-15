"""
Metrica Logistics Intelligence — KPI Computation Engine

Pure calculation functions for all six KPIs. No I/O — takes DataFrames
and config dicts, returns result dicts.

KPIs:
  1. On-Time Performance vs Promise
  2. Weekly Consistency
  3. Volatility
  4. Severity Distribution
  5. Regional Performance
  6. Peak Delta
"""

import pandas as pd


# ---------------------------------------------------------------------------
# KPI 1: On-Time Performance vs Promise
# ---------------------------------------------------------------------------

def compute_on_time_performance(df):
    """
    Compute on-time delivery rates per carrier and per carrier+service.

    Expects df to have columns: Carrier, Service_Type, on_time_flag
    Returns dict with 'overall_otd' and 'by_service' sections.
    """
    result = {"overall_otd": {}, "by_service": {}}

    # Overall per carrier
    for carrier, group in df.groupby("Carrier"):
        total = len(group)
        on_time = int(group["on_time_flag"].sum())
        late = total - on_time
        result["overall_otd"][carrier] = {
            "otd_pct": round(on_time / total * 100, 1) if total > 0 else 0,
            "total_shipments": total,
            "on_time": on_time,
            "late": late,
        }

    # Per carrier + service
    for (carrier, service), group in df.groupby(["Carrier", "Service_Type"]):
        key = f"{carrier}|{service}"
        total = len(group)
        on_time = int(group["on_time_flag"].sum())
        late = total - on_time
        result["by_service"][key] = {
            "otd_pct": round(on_time / total * 100, 1) if total > 0 else 0,
            "total_shipments": total,
            "on_time": on_time,
            "late": late,
        }

    return result


# ---------------------------------------------------------------------------
# KPI 2: Weekly Consistency
# ---------------------------------------------------------------------------

def compute_weekly_consistency(df):
    """
    Compute weekly OTD % and consistency stats per carrier.

    Expects df to have columns: Carrier, week_number, on_time_flag, Ship_DateTime
    Returns dict keyed by carrier with weekly values and stats.
    """
    result = {}

    # Create ISO week label from Ship_DateTime
    df = df.copy()
    df["iso_week_label"] = df["Ship_DateTime"].dt.isocalendar().year.astype(str) + "-W" + \
        df["Ship_DateTime"].dt.isocalendar().week.astype(str).str.zfill(2)

    for carrier, carrier_df in df.groupby("Carrier"):
        weekly = carrier_df.groupby("iso_week_label").agg(
            total=("on_time_flag", "count"),
            on_time=("on_time_flag", "sum"),
        )
        weekly["otd_pct"] = (weekly["on_time"] / weekly["total"] * 100).round(1)
        weekly = weekly.sort_index()

        values = weekly["otd_pct"].tolist()
        weeks = weekly.index.tolist()

        std_dev = round(weekly["otd_pct"].std(), 1) if len(values) > 1 else 0
        pct_above_95 = round(sum(1 for v in values if v >= 95) / len(values) * 100, 1) if values else 0
        mean_otd = round(weekly["otd_pct"].mean(), 1) if values else 0

        result[carrier] = {
            "weekly_otd_values": values,
            "weeks": weeks,
            "std_dev": std_dev,
            "pct_weeks_above_95": pct_above_95,
            "mean_weekly_otd": mean_otd,
        }

    # Also compute per carrier+service
    by_service = {}
    for (carrier, service), group_df in df.groupby(["Carrier", "Service_Type"]):
        key = f"{carrier}|{service}"
        weekly = group_df.groupby("iso_week_label").agg(
            total=("on_time_flag", "count"),
            on_time=("on_time_flag", "sum"),
        )
        weekly["otd_pct"] = (weekly["on_time"] / weekly["total"] * 100).round(1)
        weekly = weekly.sort_index()

        values = weekly["otd_pct"].tolist()
        weeks = weekly.index.tolist()
        std_dev = round(weekly["otd_pct"].std(), 1) if len(values) > 1 else 0
        pct_above_95 = round(sum(1 for v in values if v >= 95) / len(values) * 100, 1) if values else 0
        mean_otd = round(weekly["otd_pct"].mean(), 1) if values else 0

        by_service[key] = {
            "weekly_otd_values": values,
            "weeks": weeks,
            "std_dev": std_dev,
            "pct_weeks_above_95": pct_above_95,
            "mean_weekly_otd": mean_otd,
        }

    return {"by_carrier": result, "by_service": by_service}


# ---------------------------------------------------------------------------
# KPI 3: Volatility
# ---------------------------------------------------------------------------

def compute_volatility(df):
    """
    Compute min/max/range/std-dev of weekly OTD per carrier.

    Uses the same weekly aggregation as consistency.
    """
    result = {}

    df = df.copy()
    df["iso_week_label"] = df["Ship_DateTime"].dt.isocalendar().year.astype(str) + "-W" + \
        df["Ship_DateTime"].dt.isocalendar().week.astype(str).str.zfill(2)

    for carrier, carrier_df in df.groupby("Carrier"):
        weekly = carrier_df.groupby("iso_week_label").agg(
            total=("on_time_flag", "count"),
            on_time=("on_time_flag", "sum"),
        )
        weekly["otd_pct"] = (weekly["on_time"] / weekly["total"] * 100).round(1)

        values = weekly["otd_pct"]
        result[carrier] = {
            "max_weekly_otd": round(float(values.max()), 1),
            "min_weekly_otd": round(float(values.min()), 1),
            "range": round(float(values.max() - values.min()), 1),
            "std_dev": round(float(values.std()), 1) if len(values) > 1 else 0,
        }

    # Also per carrier+service
    by_service = {}
    for (carrier, service), group_df in df.groupby(["Carrier", "Service_Type"]):
        key = f"{carrier}|{service}"
        weekly = group_df.groupby("iso_week_label").agg(
            total=("on_time_flag", "count"),
            on_time=("on_time_flag", "sum"),
        )
        weekly["otd_pct"] = (weekly["on_time"] / weekly["total"] * 100).round(1)
        values = weekly["otd_pct"]
        by_service[key] = {
            "max_weekly_otd": round(float(values.max()), 1),
            "min_weekly_otd": round(float(values.min()), 1),
            "range": round(float(values.max() - values.min()), 1),
            "std_dev": round(float(values.std()), 1) if len(values) > 1 else 0,
        }

    return {"by_carrier": result, "by_service": by_service}


# ---------------------------------------------------------------------------
# KPI 4: Severity Distribution
# ---------------------------------------------------------------------------

def compute_severity_distribution(df):
    """
    For late shipments, compute delay bucket counts per carrier.

    Expects df to have columns: Carrier, on_time_flag, delay_days
    """
    result = {}

    late_df = df[~df["on_time_flag"]].copy()

    for carrier, carrier_df in late_df.groupby("Carrier"):
        total_late = len(carrier_df)
        total_all = len(df[df["Carrier"] == carrier])

        one_day = int((carrier_df["delay_days"] == 1).sum())
        two_days = int((carrier_df["delay_days"] == 2).sum())
        three_plus = int((carrier_df["delay_days"] >= 3).sum())

        result[carrier] = {
            "total_late": total_late,
            "1_day_late": {
                "count": one_day,
                "pct_of_late": round(one_day / total_late * 100, 1) if total_late else 0,
                "pct_of_total": round(one_day / total_all * 100, 1) if total_all else 0,
            },
            "2_days_late": {
                "count": two_days,
                "pct_of_late": round(two_days / total_late * 100, 1) if total_late else 0,
                "pct_of_total": round(two_days / total_all * 100, 1) if total_all else 0,
            },
            "3_plus_days_late": {
                "count": three_plus,
                "pct_of_late": round(three_plus / total_late * 100, 1) if total_late else 0,
                "pct_of_total": round(three_plus / total_all * 100, 1) if total_all else 0,
            },
        }

    return result


# ---------------------------------------------------------------------------
# KPI 5: Regional Performance
# ---------------------------------------------------------------------------

def compute_regional_performance(df, sufficiency_threshold=30):
    """
    OTD % by postcode area per carrier. Flags low-confidence regions.

    Expects df to have columns: Carrier, postcode_area, on_time_flag
    """
    result = {}

    for carrier, carrier_df in df.groupby("Carrier"):
        regional = carrier_df.groupby("postcode_area").agg(
            shipments=("on_time_flag", "count"),
            on_time=("on_time_flag", "sum"),
        )
        regional["otd_pct"] = (regional["on_time"] / regional["shipments"] * 100).round(1)
        regional["confidence"] = regional["shipments"].apply(
            lambda x: "high" if x >= sufficiency_threshold else "low"
        )
        regional = regional.sort_values("otd_pct", ascending=False)

        regions = []
        for area, row in regional.iterrows():
            regions.append({
                "postcode_area": area,
                "otd_pct": float(row["otd_pct"]),
                "shipments": int(row["shipments"]),
                "confidence": row["confidence"],
            })

        # Top/bottom 5 (only from high-confidence regions)
        high_conf = [r for r in regions if r["confidence"] == "high"]
        top_5 = [r["postcode_area"] for r in high_conf[:5]]
        bottom_5 = [r["postcode_area"] for r in high_conf[-5:]]

        result[carrier] = {
            "regions": regions,
            "top_5": top_5,
            "bottom_5": bottom_5,
        }

    return result


# ---------------------------------------------------------------------------
# KPI 6: Peak Delta
# ---------------------------------------------------------------------------

def compute_peak_delta(df):
    """
    Compare peak vs non-peak OTD per carrier.

    Expects df to have columns: Carrier, Service_Type, peak_flag, on_time_flag
    """
    result = {"by_carrier": {}, "by_service": {}}

    for carrier, carrier_df in df.groupby("Carrier"):
        peak = carrier_df[carrier_df["peak_flag"]]
        non_peak = carrier_df[~carrier_df["peak_flag"]]

        peak_otd = round(peak["on_time_flag"].mean() * 100, 1) if len(peak) else 0
        non_peak_otd = round(non_peak["on_time_flag"].mean() * 100, 1) if len(non_peak) else 0

        result["by_carrier"][carrier] = {
            "peak_otd": peak_otd,
            "non_peak_otd": non_peak_otd,
            "delta": round(peak_otd - non_peak_otd, 1),
            "peak_shipments": len(peak),
            "non_peak_shipments": len(non_peak),
        }

    for (carrier, service), group_df in df.groupby(["Carrier", "Service_Type"]):
        key = f"{carrier}|{service}"
        peak = group_df[group_df["peak_flag"]]
        non_peak = group_df[~group_df["peak_flag"]]

        peak_otd = round(peak["on_time_flag"].mean() * 100, 1) if len(peak) else 0
        non_peak_otd = round(non_peak["on_time_flag"].mean() * 100, 1) if len(non_peak) else 0

        result["by_service"][key] = {
            "peak_otd": peak_otd,
            "non_peak_otd": non_peak_otd,
            "delta": round(peak_otd - non_peak_otd, 1),
            "peak_shipments": len(peak),
            "non_peak_shipments": len(non_peak),
        }

    return result


# ---------------------------------------------------------------------------
# Trade-offs — programmatic comparison
# ---------------------------------------------------------------------------

def compute_trade_offs(on_time, consistency, volatility, regional, peak_delta):
    """
    Compare carriers across all KPIs and determine which is best at what.
    Returns a dict of trade-off labels.
    """
    carriers = list(on_time["overall_otd"].keys())
    if len(carriers) < 2:
        return {}

    c1, c2 = carriers[0], carriers[1]

    # Best overall OTD
    best_otd = c1 if on_time["overall_otd"][c1]["otd_pct"] >= on_time["overall_otd"][c2]["otd_pct"] else c2

    # Best consistency (lower std_dev is better)
    cons = consistency["by_carrier"]
    best_consistency = c1 if cons[c1]["std_dev"] <= cons[c2]["std_dev"] else c2

    # Best standard service
    std_key_1 = f"{c1}|Standard"
    std_key_2 = f"{c2}|Standard"
    best_standard = c1
    if std_key_1 in on_time["by_service"] and std_key_2 in on_time["by_service"]:
        best_standard = c1 if on_time["by_service"][std_key_1]["otd_pct"] >= on_time["by_service"][std_key_2]["otd_pct"] else c2

    # Best rural coverage — average OTD in rural postcode areas
    rural_areas = {"AB", "DD", "FK", "KY", "PA", "IV", "PH", "LL", "SA", "SY", "LD"}

    def rural_avg(carrier_regions):
        rural = [r for r in carrier_regions["regions"]
                 if r["postcode_area"] in rural_areas and r["confidence"] == "high"]
        if not rural:
            return 0
        return sum(r["otd_pct"] for r in rural) / len(rural)

    rural_1 = rural_avg(regional[c1])
    rural_2 = rural_avg(regional[c2])
    best_rural = c1 if rural_1 >= rural_2 else c2

    # Best peak resilience (smallest absolute delta is better)
    pd1 = peak_delta["by_carrier"][c1]
    pd2 = peak_delta["by_carrier"][c2]
    best_peak = c1 if abs(pd1["delta"]) <= abs(pd2["delta"]) else c2

    # Highest risk
    vol = volatility["by_carrier"]
    worst_vol = c1 if vol[c1]["range"] > vol[c2]["range"] else c2
    worst_peak = c1 if abs(pd1["delta"]) > abs(pd2["delta"]) else c2
    highest_risk = f"{worst_peak} (peak volatility)"

    return {
        "best_overall_otd": best_otd,
        "best_consistency": best_consistency,
        "best_standard_service": best_standard,
        "best_rural_coverage": best_rural,
        "best_peak_resilience": best_peak,
        "highest_risk": highest_risk,
    }

"""
Metrica Logistics Intelligence — Report PDF Generator

Loads KPI data, renders an HTML report via Jinja2 templates,
and converts it to a print-ready A4 PDF using Playwright.

Usage:
    python scripts/generate_report_pdf.py \
        --kpis output/kpis.json \
        --config scripts/config/report_request.json \
        --output output/report.pdf
"""

import argparse
import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Add the templates directory to the path so we can import charts.py
sys.path.insert(0, str(Path(__file__).parent / "templates"))
from charts import bar_chart_otd, line_chart_weekly, severity_bars, delta_indicator


def load_json(path):
    with open(path) as f:
        return json.load(f)


def generate_tldr(trade_offs, kpis):
    """
    Generate a 2-3 sentence TL;DR summary from the trade-offs and KPIs.
    Neutral, evidence-based, decision-oriented tone.
    """
    best_otd = trade_offs["best_overall_otd"]
    best_consistency = trade_offs["best_consistency"]
    best_peak = trade_offs["best_peak_resilience"]
    best_standard = trade_offs["best_standard_service"]
    best_rural = trade_offs["best_rural_coverage"]
    highest_risk = trade_offs["highest_risk"]

    carriers = list(kpis["on_time_performance"]["overall_otd"].keys())
    peak = kpis["peak_delta"]["by_carrier"]

    # Determine which carrier is the "consistent" one and which is the "variable" one
    consistent_carrier = best_consistency
    other_carrier = [c for c in carriers if c != consistent_carrier][0]

    sentences = []

    # Sentence 1: Strengths of the consistent carrier
    consistency_strengths = []
    if best_consistency == best_peak:
        consistency_strengths.append(
            "delivers more consistently across both services and maintains stronger "
            "performance during peak trading periods"
        )
    else:
        consistency_strengths.append("delivers more consistently across both services")

    sentences.append(f"{consistent_carrier} {consistency_strengths[0]}.")

    # Sentence 2: Strengths of the other carrier
    other_strengths = []
    if best_standard == other_carrier:
        other_strengths.append("outperforms on standard deliveries")
    if best_rural == other_carrier:
        other_strengths.append("provides better coverage in rural postcode areas")
    if other_strengths:
        sentences.append(f"{other_carrier} {' and '.join(other_strengths)}.")

    # Sentence 3: Key risk
    risk_carrier = highest_risk.split(" (")[0]
    risk_peak_delta = abs(peak[risk_carrier]["delta"])
    safe_carrier = [c for c in carriers if c != risk_carrier][0]
    safe_peak_delta = abs(peak[safe_carrier]["delta"])
    sentences.append(
        f"The key risk is {risk_carrier}'s significantly higher volatility during peak, "
        f"with on-time performance dropping {risk_peak_delta} percentage points compared to "
        f"{safe_carrier}'s {safe_peak_delta} point decline."
    )

    return " ".join(sentences)


def build_promises_dict(config_path):
    """Load promises config and return as a dict keyed by (carrier, service)."""
    with open(config_path) as f:
        data = json.load(f)
    result = {}
    for p in data["promises"]:
        key = (p["carrier_name"], p["service_name"])
        result[key] = p
    return result


def render_html(kpis, config, promises):
    """Render the Jinja2 HTML report template with all data."""
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("report.html")

    # Load CSS
    css_path = templates_dir / "styles.css"
    with open(css_path) as f:
        css = f.read()

    # Generate charts
    otd_chart = bar_chart_otd(kpis["on_time_performance"])
    weekly_chart = line_chart_weekly(kpis["weekly_consistency"])
    sev_chart = severity_bars(kpis["severity_distribution"])

    # Generate TL;DR
    tldr = generate_tldr(kpis["trade_offs"], kpis)

    # Render
    html = template.render(
        css=css,
        metadata=kpis["metadata"],
        tldr=tldr,
        on_time=kpis["on_time_performance"],
        consistency=kpis["weekly_consistency"],
        volatility=kpis["volatility"],
        severity=kpis["severity_distribution"],
        regional=kpis["regional_performance"],
        peak_delta=kpis["peak_delta"],
        trade_offs=kpis["trade_offs"],
        promises=promises,
        sufficiency_threshold=config.get("data_sufficiency_threshold", 30),
        otd_bar_chart=otd_chart,
        weekly_line_chart=weekly_chart,
        severity_chart=sev_chart,
        delta_indicator=delta_indicator,
    )

    return html


def find_chromium():
    """Find a Chromium executable, preferring Playwright's bundled version."""
    import glob
    import shutil

    # Check Playwright's standard locations
    for pattern in [
        "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
        "/opt/pw-browsers/chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell",
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]  # latest version

    # Fall back to system chromium
    for name in ["chromium-browser", "chromium", "google-chrome"]:
        path = shutil.which(name)
        if path:
            return path

    return None


def html_to_pdf(html_content, output_path):
    """Convert HTML string to PDF using Playwright."""
    from playwright.sync_api import sync_playwright

    chromium_path = find_chromium()

    with sync_playwright() as p:
        launch_kwargs = {}
        if chromium_path:
            launch_kwargs["executable_path"] = chromium_path
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")

        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={
                "top": "0mm",
                "bottom": "0mm",
                "left": "0mm",
                "right": "0mm",
            },
        )
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Generate Metrica report PDF")
    parser.add_argument("--kpis", required=True, help="Path to kpis.json")
    parser.add_argument("--config", required=True, help="Path to report_request.json")
    parser.add_argument("--output", required=True, help="Output PDF path")
    args = parser.parse_args()

    print("Loading KPI data...")
    kpis = load_json(args.kpis)
    config = load_json(args.config)

    # Load promises from the standard location
    promises_path = Path(args.config).parent / "carrier_promises.json"
    promises = build_promises_dict(promises_path)

    print("Rendering HTML report...")
    html = render_html(kpis, config, promises)

    # Save HTML for debugging
    html_path = Path(args.output).with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  HTML saved to {html_path}")

    print("Converting to PDF via Playwright...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_to_pdf(html, output_path)

    print(f"\nDone! Report PDF written to {output_path}")


if __name__ == "__main__":
    main()

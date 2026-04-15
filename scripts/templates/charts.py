"""
Metrica Logistics Intelligence — Inline SVG Chart Generator

Generates simple SVG charts for embedding in the PDF report template.
No JavaScript chart libraries — pure SVG strings.
"""


# Colour palette
CARRIER_COLOURS = {
    "Carrier A": "#3b82f6",   # blue
    "Carrier B": "#0f172a",   # navy
}
CARRIER_COLOURS_LIGHT = {
    "Carrier A": "#93c5fd",
    "Carrier B": "#64748b",
}
GREEN = "#16a34a"
RED = "#dc2626"
AMBER = "#d97706"
GRID_COLOUR = "#e2e8f0"
TEXT_COLOUR = "#475569"


def bar_chart_otd(on_time_data, width=540, height=280):
    """
    Grouped bar chart: OTD % per carrier+service.
    4 bars: A Next Day, A Standard, B Next Day, B Standard.
    """
    by_service = on_time_data["by_service"]
    bars = []
    labels = []
    for key in sorted(by_service.keys()):
        carrier, service = key.split("|")
        bars.append({
            "label": f"{carrier}\n{service}",
            "short_label": f"{service}",
            "carrier": carrier,
            "value": by_service[key]["otd_pct"],
        })
        labels.append(f"{carrier} — {service}")

    margin_left = 50
    margin_right = 20
    margin_top = 30
    margin_bottom = 70
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom

    n = len(bars)
    bar_width = min(60, chart_w / n * 0.6)
    gap = (chart_w - bar_width * n) / (n + 1)

    # Y axis: 0 to 100
    y_min, y_max = 0, 100

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="font-family: Inter, system-ui, sans-serif;">'
    ]

    # Grid lines
    for pct in [0, 25, 50, 75, 100]:
        y = margin_top + chart_h - (pct / 100 * chart_h)
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" '
            f'stroke="{GRID_COLOUR}" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{margin_left - 8}" y="{y + 4}" text-anchor="end" '
            f'fill="{TEXT_COLOUR}" font-size="11">{pct}%</text>'
        )

    # Bars
    for i, bar in enumerate(bars):
        x = margin_left + gap + i * (bar_width + gap)
        bar_h = (bar["value"] / 100) * chart_h
        y = margin_top + chart_h - bar_h

        colour = CARRIER_COLOURS.get(bar["carrier"], "#3b82f6")
        svg_parts.append(
            f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" '
            f'fill="{colour}" rx="3"/>'
        )
        # Value on top
        svg_parts.append(
            f'<text x="{x + bar_width / 2}" y="{y - 6}" text-anchor="middle" '
            f'fill="{TEXT_COLOUR}" font-size="12" font-weight="600">{bar["value"]}%</text>'
        )
        # Label below
        carrier_short = bar["carrier"].replace("Carrier ", "")
        svg_parts.append(
            f'<text x="{x + bar_width / 2}" y="{margin_top + chart_h + 18}" '
            f'text-anchor="middle" fill="{TEXT_COLOUR}" font-size="10">{bar["short_label"]}</text>'
        )
        svg_parts.append(
            f'<text x="{x + bar_width / 2}" y="{margin_top + chart_h + 32}" '
            f'text-anchor="middle" fill="{TEXT_COLOUR}" font-size="10" font-weight="600">'
            f'Carrier {carrier_short}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def line_chart_weekly(consistency_data, width=540, height=300):
    """
    Line chart: Weekly OTD % over time, one line per carrier.
    X-axis: weeks, Y-axis: OTD %.
    """
    by_carrier = consistency_data["by_carrier"]
    carriers = sorted(by_carrier.keys())

    margin_left = 50
    margin_right = 20
    margin_top = 30
    margin_bottom = 50
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom

    # Determine Y range — fit to data with padding
    all_values = []
    for c in carriers:
        all_values.extend(by_carrier[c]["weekly_otd_values"])
    y_min_data = min(all_values) if all_values else 0
    y_max_data = max(all_values) if all_values else 100
    y_min = max(0, int(y_min_data / 5) * 5 - 5)
    y_max = min(100, int(y_max_data / 5) * 5 + 10)
    y_range = y_max - y_min

    # X positions — use the longest week list
    max_weeks = max(len(by_carrier[c]["weeks"]) for c in carriers)

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="font-family: Inter, system-ui, sans-serif;">'
    ]

    # Grid lines
    step = 5 if y_range <= 30 else 10
    for pct in range(y_min, y_max + 1, step):
        y = margin_top + chart_h - ((pct - y_min) / y_range * chart_h)
        svg_parts.append(
            f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" '
            f'stroke="{GRID_COLOUR}" stroke-width="1"/>'
        )
        svg_parts.append(
            f'<text x="{margin_left - 8}" y="{y + 4}" text-anchor="end" '
            f'fill="{TEXT_COLOUR}" font-size="10">{pct}%</text>'
        )

    # Lines per carrier
    for carrier in carriers:
        values = by_carrier[carrier]["weekly_otd_values"]
        weeks = by_carrier[carrier]["weeks"]
        n = len(values)
        if n == 0:
            continue

        colour = CARRIER_COLOURS.get(carrier, "#3b82f6")
        points = []
        for i, val in enumerate(values):
            x = margin_left + (i / max(1, max_weeks - 1)) * chart_w
            y = margin_top + chart_h - ((val - y_min) / y_range * chart_h)
            points.append(f"{x:.1f},{y:.1f}")

        svg_parts.append(
            f'<polyline points="{" ".join(points)}" fill="none" '
            f'stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>'
        )

    # X axis labels (show every ~10th week)
    if max_weeks > 0:
        sample_weeks = by_carrier[carriers[0]]["weeks"]
        label_interval = max(1, max_weeks // 8)
        for i in range(0, len(sample_weeks), label_interval):
            x = margin_left + (i / max(1, max_weeks - 1)) * chart_w
            # Show just the week number part
            label = sample_weeks[i].split("-W")[1] if "-W" in sample_weeks[i] else sample_weeks[i]
            svg_parts.append(
                f'<text x="{x}" y="{margin_top + chart_h + 18}" text-anchor="middle" '
                f'fill="{TEXT_COLOUR}" font-size="9">W{label}</text>'
            )

    # Legend
    legend_y = margin_top + chart_h + 38
    for i, carrier in enumerate(carriers):
        lx = margin_left + i * 150
        colour = CARRIER_COLOURS.get(carrier, "#3b82f6")
        svg_parts.append(
            f'<rect x="{lx}" y="{legend_y - 8}" width="12" height="12" fill="{colour}" rx="2"/>'
        )
        svg_parts.append(
            f'<text x="{lx + 16}" y="{legend_y + 2}" fill="{TEXT_COLOUR}" font-size="11">'
            f'{carrier}</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def severity_bars(severity_data, width=540, height=200):
    """
    Horizontal stacked bar chart showing late-shipment severity per carrier.
    """
    carriers = sorted(severity_data.keys())

    margin_left = 80
    margin_right = 30
    margin_top = 30
    margin_bottom = 40
    chart_w = width - margin_left - margin_right
    bar_height = 36
    gap = 20

    total_h = margin_top + len(carriers) * (bar_height + gap) + margin_bottom

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
        f'viewBox="0 0 {width} {total_h}" style="font-family: Inter, system-ui, sans-serif;">'
    ]

    buckets = ["1_day_late", "2_days_late", "3_plus_days_late"]
    bucket_labels = ["1 day", "2 days", "3+ days"]
    bucket_colours = ["#93c5fd", "#3b82f6", "#0f172a"]

    for ci, carrier in enumerate(carriers):
        y = margin_top + ci * (bar_height + gap)
        data = severity_data[carrier]
        total_late = data["total_late"]
        if total_late == 0:
            continue

        # Carrier label
        svg_parts.append(
            f'<text x="{margin_left - 8}" y="{y + bar_height / 2 + 4}" text-anchor="end" '
            f'fill="{TEXT_COLOUR}" font-size="12" font-weight="600">{carrier}</text>'
        )

        # Stacked bars
        x_offset = margin_left
        for bi, bucket in enumerate(buckets):
            count = data[bucket]["count"]
            pct = count / total_late if total_late else 0
            seg_w = pct * chart_w

            svg_parts.append(
                f'<rect x="{x_offset}" y="{y}" width="{seg_w}" height="{bar_height}" '
                f'fill="{bucket_colours[bi]}"/>'
            )
            if seg_w > 40:
                svg_parts.append(
                    f'<text x="{x_offset + seg_w / 2}" y="{y + bar_height / 2 + 4}" '
                    f'text-anchor="middle" fill="white" font-size="11">'
                    f'{data[bucket]["pct_of_late"]:.0f}%</text>'
                )
            x_offset += seg_w

    # Legend
    legend_y = margin_top + len(carriers) * (bar_height + gap) + 8
    for i, (label, colour) in enumerate(zip(bucket_labels, bucket_colours)):
        lx = margin_left + i * 120
        svg_parts.append(
            f'<rect x="{lx}" y="{legend_y}" width="12" height="12" fill="{colour}" rx="2"/>'
        )
        svg_parts.append(
            f'<text x="{lx + 16}" y="{legend_y + 10}" fill="{TEXT_COLOUR}" font-size="11">'
            f'{label} late</text>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def delta_indicator(value, suffix="pp"):
    """Return an HTML span with colour-coded delta value."""
    if value > 0:
        colour = GREEN
        prefix = "+"
    elif value < 0:
        colour = RED
        prefix = ""
    else:
        colour = TEXT_COLOUR
        prefix = ""
    return f'<span style="color: {colour}; font-weight: 700;">{prefix}{value}{suffix}</span>'

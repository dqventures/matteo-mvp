# Metrica Report Delivery — Operator Runbook

Step-by-step guide to deliver a carrier performance comparison report.

---

## Prerequisites

Before your first report, install these once:

```bash
# Python 3.11+
python3 --version

# pip packages
pip install pandas jinja2 playwright

# Playwright browser
playwright install chromium

# Node.js 18+ (for the website)
node --version

# Website dependencies
cd web && npm install && cd ..
```

---

## Step 1: After the Discovery Call

Fill in these two config files based on what you learn on the call.

### scripts/config/report_request.json

```json
{
  "customer_name": "Acme Retail Ltd",        // Customer's company name
  "report_title": "Carrier Performance Comparison",  // Usually keep default
  "period_start": "2025-01-01",              // Start of analysis period (YYYY-MM-DD)
  "period_end": "2025-12-31",                // End of analysis period
  "geography_scope": "UK",                   // Always "UK" for now
  "carriers_in_scope": ["Carrier A", "Carrier B"],   // Carrier names as they appear in the data
  "services_in_scope": ["Next Day", "Standard"],     // Service types in the data
  "intent": "tendering",                     // "tendering" includes peak analysis
  "peak_start": "2025-11-15",               // Start of peak window
  "peak_end": "2025-12-23",                 // End of peak window
  "data_sufficiency_threshold": 30,          // Min shipments per slice (keep at 30)
  "generated_date": "2026-04-15"             // Today's date
}
```

### scripts/config/carrier_promises.json

Update the carrier names and promise definitions to match the customer's carriers:

```json
{
  "promises": [
    {
      "carrier_name": "Carrier A",           // Must match the data exactly
      "service_name": "Next Day",            // Must match the data exactly
      "promised_transit_days": 1,            // SLA in transit days
      "promised_day_type": "working_days",   // "working_days" or "calendar_days"
      "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    }
    // ... add one entry per carrier+service combination
  ]
}
```

**Key decisions:**
- `promised_day_type`: Use "working_days" if the carrier's SLA excludes weekends. Use "calendar_days" if the SLA counts every day.
- `working_days`: Which days count. Most UK carriers are Mon-Fri. Some include Saturday for premium services.

---

## Step 2: Get and Validate Data

Place the provider's CSV file in the `data/` directory:

```bash
# Create data directory if it doesn't exist
mkdir -p data

# Copy the file (adjust the source path)
cp ~/Downloads/shipment_data.csv data/provider_extract.csv
```

**Required CSV columns:**
- `Shipment_ID` — unique identifier per shipment
- `Carrier` — carrier name (must match config)
- `Service_Type` — service name (must match config)
- `Ship_DateTime` — dispatch date/time (ISO 8601, e.g. "2025-03-15T09:30:00Z")
- `Delivered_DateTime` — delivery date/time (blank for undelivered)
- `Promised_Delivery_DateTime` — promised delivery date/time
- `Shipment_Status` — "Delivered", "Failed", "Returned", or "Lost"
- `Destination_Postcode` — UK postcode area + district (e.g. "SW1", "BA2")

Run validation:

```bash
python scripts/validate_data.py data/provider_extract.csv \
  --config scripts/config/report_request.json \
  --promises scripts/config/carrier_promises.json
```

**If PASS** → continue to Step 3.

**If FAIL** → read the error messages. Common issues:
- Column names don't match → rename columns in the CSV
- Carrier names don't match config → update `carrier_promises.json`
- Date parsing fails → check the date format in the CSV
- Not enough data → ask the provider for more data or lower the threshold

---

## Step 3: Generate KPIs

```bash
python scripts/compute_report.py \
  --data data/provider_extract.csv \
  --config scripts/config/report_request.json \
  --promises scripts/config/carrier_promises.json \
  --output output/kpis.json
```

**Sanity checks after running:**
- Open `output/kpis.json` and look at the `on_time_performance.overall_otd` section
- Do the OTD percentages look realistic? (Typically 80-98% for UK carriers)
- Does the `trade_offs` section make sense given what you know about the carriers?
- Are the `peak_delta` values negative? (Performance should drop during peak)

---

## Step 4: Generate Report PDF

```bash
python scripts/generate_report_pdf.py \
  --kpis output/kpis.json \
  --config scripts/config/report_request.json \
  --output output/report.pdf
```

**Review the PDF:**
1. Open `output/report.pdf`
2. Check all 8 pages render correctly
3. Verify the TL;DR summary on page 1 is accurate
4. Check charts display properly
5. Verify regional data tables look reasonable
6. Read the method page to ensure it matches the customer's setup

---

## Step 5: Upload and Share

### 5a. Copy the report to the web directory

```bash
# Use a descriptive filename
cp output/report.pdf web/public/reports/acme-retail-2026.pdf
```

### 5b. Generate a unique token

```bash
python3 -c "import uuid; print(uuid.uuid4())"
```

This prints something like: `f47ac10b-58cc-4372-a567-0e02b2c3d479`

### 5c. Add token to the portal

Edit `web/data/tokens.json` and add a new entry:

```json
{
  "existing-token-here": { ... },
  "f47ac10b-58cc-4372-a567-0e02b2c3d479": {
    "customer_name": "Acme Retail Ltd",
    "report_file": "acme-retail-2026.pdf",
    "created_at": "2026-04-15",
    "expires_at": "2026-07-15"
  }
}
```

Set `expires_at` to 90 days from now.

### 5d. Deploy

```bash
cd web
vercel --prod
```

### 5e. Send the link

Send the customer this URL:
```
https://metrica.ai/report/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

---

## Quick Reference: Testing with Synthetic Data

To test the full pipeline with fake data:

```bash
# 1. Generate synthetic data
python scripts/generate_synthetic_data.py

# 2. Validate it
python scripts/validate_data.py output/synthetic_shipments.csv \
  --config scripts/config/report_request.json \
  --promises scripts/config/carrier_promises.json

# 3. Compute KPIs
python scripts/compute_report.py \
  --data output/synthetic_shipments.csv \
  --config scripts/config/report_request.json \
  --promises scripts/config/carrier_promises.json \
  --output output/kpis.json

# 4. Generate PDF
python scripts/generate_report_pdf.py \
  --kpis output/kpis.json \
  --config scripts/config/report_request.json \
  --output output/report.pdf
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'pandas'` | Run `pip install pandas` |
| `playwright._impl._errors.Error: Executable doesn't exist` | Run `playwright install chromium` |
| Validation says "Unknown carriers" | Carrier names in CSV must exactly match `carrier_promises.json` |
| PDF is blank or missing charts | Check `output/report.html` in a browser — the HTML should render correctly |
| Portal shows "Report not found" | Check the token in `web/data/tokens.json` matches the URL exactly |
| `vercel` command not found | Run `npm install -g vercel` |

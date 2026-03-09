# Claude Task: Update CT Trout Stocking Data

Paste or reference this file when you want Claude to fetch and parse the latest
CT DEEP stocking report. Everything Claude needs is in this document.

---

## Task

1. **Download** the current stocking report PDF from:
   `https://portal.ct.gov/-/media/deep/fishing/weekly_reports/currentstockingreport.pdf`

2. **Save** a copy to `pdf/` using today's date:
   `pdf/YYYY-MM-DD-CurrentStockingReport.pdf`
   (use today's date, not the report date — this records when you pulled it)

3. **Parse** the PDF and write `stocking_data.json`

4. **Print** a validation summary when done

---

## What to Extract

### From the page 1 intro text

- **Report date**: the date in `STOCKING UPDATE AS OF MM/DD/YYYY`
- **Catch & release end date**: the April date in the phrase
  "until 6:00 am on the second Saturday of April (April Nth this year)"
  → format as `YYYY-MM-DDTHH:MM:SS` with time `06:00:00`

### From Table 1 (alphabetical by waterbody name)

Stop at "Table 2: Sorted By Town" — that section is redundant.

Each row has three columns: **Waterbody**, **Town(s)**, **Stocked**

| Raw cell | Parse into |
|----------|-----------|
| `Amos Lake – TML` | waterbody: `Amos Lake`, management_type: `TML` |
| `Blackberry River – WTMA class 3 (and Open)` | waterbody: `Blackberry River`, management_type: `WTMA class 3 (and Open)` |
| `Farmington River - TMA (Lower Collinsville to RT 177 )` | waterbody: `Farmington River`, management_type: `TMA (Lower Collinsville to RT 177)` |
| `Ball Pond` | waterbody: `Ball Pond`, management_type: `null` |
| `Easton, Fairfield, Weston` | towns: `["Easton", "Fairfield", "Weston"]` |
| `3/3, 3/4` | stocked_dates: `["YYYY-03-03", "YYYY-03-04"]` (use report year) |
| *(blank)* | stocked_dates: `[]` |

Split waterbody from management type on ` – ` (en dash) or ` - ` (hyphen with
spaces) or ` -` followed immediately by an uppercase letter. Everything before
the separator is the waterbody name; everything after is the management type.

---

## Output: stocking_data.json

```json
{
  "report_date": "YYYY-MM-DD",
  "source": "CT DEEP Fisheries Division Spring YYYY",
  "season": "Spring YYYY",
  "catch_and_release_until": "YYYY-MM-DDTHH:MM:SS",
  "recently_stocked": [
    {
      "date": "YYYY-MM-DD",
      "locations": [
        {
          "waterbody": "Ball Pond",
          "towns": ["New Fairfield"],
          "management_type": null
        }
      ]
    }
  ],
  "all_locations": [
    {
      "waterbody": "Amos Lake",
      "towns": ["Preston"],
      "management_type": "TML",
      "stocked_dates": ["YYYY-MM-DD"]
    }
  ]
}
```

Rules:
- `recently_stocked`: only locations that have been stocked, grouped by date,
  newest date first
- `all_locations`: every location in Table 1 (stocked or not), alphabetical
- Both lists include `management_type` (string or null)

---

## Validation Summary to Print

```
PDF saved:              pdf/YYYY-MM-DD-CurrentStockingReport.pdf
Report date:            YYYY-MM-DD
Catch & release until:  YYYY-MM-DD 06:00
Total locations:        NNN  (expect ~250+)
Stocked so far:         NN
Stocking dates seen:    YYYY-MM-DD, YYYY-MM-DD, ...

First 5 stocked (closest dates first):
  - Waterbody Name (Town) [MgmtType] — YYYY-MM-DD
```

---

## Notes

- The PDF URL always points to the current report — CT DEEP overwrites it each update
- The report date in the PDF may be a few days behind today's date (that's normal)
- Management type abbreviations: TML, TMA, TTA, TP, WTMA, CFW
- Some waterbodies span multiple towns — keep all towns in the list
- Waterbody names are the canonical key; don't alter them beyond stripping the mgmt suffix

# How to Update CT Trout Stocking Data

Three ways to update `stocking_data.json` with the latest CT DEEP report.
Pick the one that fits your situation.

---

## Option A — Ask Claude (simplest)

Open a Claude Code session in this directory and say:

> "Follow the instructions in `claude_task.md`"

Claude will fetch the PDF, save a dated copy in `pdf/`, parse it, and write
`stocking_data.json`. No scripts, no dependencies, handles format changes
gracefully.

**When to use:** Ad-hoc updates, when CT DEEP changes their PDF format,
or when you just want it done without thinking about it.

---

## Option B — Python script (fastest, no API cost)

```bash
.venv/bin/python3 parse_pdf.py
```

Reads the most recently modified PDF in `pdf/` and writes `stocking_data.json`.
Does not download anything — you need to have a PDF in `pdf/` already.

To download + parse in one step:
```bash
.venv/bin/python3 compare_parse.py --no-download
# or, to also fetch fresh:
.venv/bin/python3 compare_parse.py
```

**When to use:** Automation, cron jobs, or when you already have the PDF
and want a quick refresh.

---

## Option C — Comparison run (experiment)

```bash
export ANTHROPIC_API_KEY=your_key_here
.venv/bin/python3 compare_parse.py
```

Downloads the current PDF, runs both the Python parser and Claude API, prints
a side-by-side comparison, and appends a record to `parse_history.md`.

**When to use:** Validating a new PDF format, checking if the Python parser
has drifted, or just curious which approach is more accurate right now.

---

## Files at a Glance

| File | Purpose |
|------|---------|
| `claude_task.md` | Self-contained prompt — give this to Claude for Option A |
| `parse_pdf.py` | Python parser — reads PDFs, writes stocking_data.json |
| `compare_parse.py` | Comparison runner — downloads PDF, runs both parsers, logs results |
| `parse_history.md` | Running log of comparison results across PDF updates |
| `stocking_data.json` | The parsed output — what all other scripts read |
| `pdf/` | Saved PDF copies, named `YYYY-MM-DD-CurrentStockingReport.pdf` |

---

## PDF Naming Convention

```
pdf/YYYY-MM-DD-CurrentStockingReport.pdf
```

The date is **when you pulled it**, not the report date inside the PDF.
CT DEEP updates the same URL in-place, so the filename is how you track history.
The report date (from inside the PDF) is stored in `stocking_data.json`.

---

## Data Flow

```
CT DEEP URL
    │
    ▼
pdf/YYYY-MM-DD-CurrentStockingReport.pdf   ← saved copy
    │
    ├── parse_pdf.py (Python)
    │       └── stocking_data.json
    │
    └── Claude API (claude_task.md prompt)
            └── stocking_data.json
```

---

## Viewing Results

```bash
.venv/bin/python3 map_stocked.py          # compact list with Google Maps links
.venv/bin/python3 find_stocked.py         # detailed view with distances
.venv/bin/python3 generate_kml.py         # KML for Google Maps import
```

---

## CT DEEP PDF URL

`https://portal.ct.gov/-/media/deep/fishing/weekly_reports/currentstockingreport.pdf`

This URL is permanent — the file is overwritten in place with each update.
CT DEEP typically updates it every few days during stocking season (March–May).

# CT Trout Stocking — Parse Comparison History

Each entry records one comparison run: Python script vs Claude API.
Goal: understand when each approach is more accurate or reliable over time.

The Python parser (`parse_pdf.py`) uses `pdfplumber` table extraction + regex.
The Claude parser sends the raw table text to `claude-sonnet-4-6` via API.

---


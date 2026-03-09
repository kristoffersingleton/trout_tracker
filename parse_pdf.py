#!/usr/bin/env python3
"""
Parse the latest CT DEEP trout stocking PDF and update stocking_data.json.

Finds the most recent PDF in the pdf/ directory, extracts stocking data
from Table 1 (sorted by waterbody), and writes stocking_data.json.
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pdfplumber

BASE = Path(__file__).parent
PDF_DIR = BASE / "pdf"
OUTPUT = BASE / "stocking_data.json"


def find_latest_pdf():
    """Return the most recently modified PDF in the pdf/ directory."""
    pdfs = [p for p in PDF_DIR.glob("*.pdf") if not p.name.endswith(".pdf:Zone.Identifier")]
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found in {PDF_DIR}")
    return max(pdfs, key=lambda p: p.stat().st_mtime)


def parse_report_date(text):
    """Extract report date from page 1 text. Returns 'YYYY-MM-DD'."""
    m = re.search(r"STOCKING UPDATE AS OF (\d{2})/(\d{2})/(\d{4})", text)
    if not m:
        raise ValueError("Could not find report date in PDF")
    month, day, year = m.group(1), m.group(2), m.group(3)
    return f"{year}-{month}-{day}"


def parse_catch_release_date(text, year):
    """Extract catch-and-release end date from page 1 text. Returns ISO datetime string."""
    # Look for "until 6:00 am on ... April (April 11th" or "until ... April 11"
    m = re.search(r"until\b.*?\bApril\s+\(?April\s+(\d+)", text, re.DOTALL)
    if not m:
        m = re.search(r"until\b.*?\b(April)\s+(\d+)", text, re.DOTALL)
        if m:
            return f"{year}-04-{int(m.group(2)):02d}T06:00:00"
        return f"{year}-04-11T06:00:00"  # fallback
    return f"{year}-04-{int(m.group(1)):02d}T06:00:00"


def parse_stocked_dates(dates_str, year):
    """Convert stocked date string like '3/2' or '3/3, 3/4' to list of 'YYYY-MM-DD'."""
    if not dates_str or not dates_str.strip():
        return []
    results = []
    for part in dates_str.split(","):
        part = part.strip()
        m = re.match(r"(\d+)/(\d+)", part)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            results.append(f"{year}-{month:02d}-{day:02d}")
    return results


def parse_waterbody(cell):
    """Split 'Name – ManagementType' into (name, management_type)."""
    # Try em dash or spaced dash first, then unspaced dash before uppercase
    m = re.search(r" [–\-] (.+)$", cell)
    if m:
        name = cell[:m.start()].strip()
        mgmt = m.group(1).strip()
        return name, mgmt
    # Handle " -TML" (no space after dash, followed by uppercase)
    m = re.search(r" -([A-Z].*)$", cell)
    if m:
        name = cell[:m.start()].strip()
        mgmt = m.group(1).strip()
        return name, mgmt
    return cell.strip(), None


def is_table2_header(row):
    """Detect the Table 2 header row (marks end of Table 1 data)."""
    if not row or not row[0]:
        return False
    cell = row[0].strip()
    # Table 2 header: "Waterbody – Management type" without "(Alphabetically)"
    return cell.startswith("Waterbody") and "Alphabetically" not in cell


def is_table1_header(row):
    """Detect the Table 1 header row (to skip)."""
    if not row or not row[0]:
        return False
    return "Alphabetically" in (row[0] or "")


def parse_pdf(pdf_path):
    """Parse stocking data from PDF. Returns (report_date, catch_release, locations)."""
    with pdfplumber.open(pdf_path) as pdf:
        page1_text = pdf.pages[0].extract_text() or ""
        report_date = parse_report_date(page1_text)
        year = report_date[:4]
        catch_release = parse_catch_release_date(page1_text, year)

        rows = []
        done = False
        for page in pdf.pages[1:]:  # Skip page 1 (intro text)
            if done:
                break
            for table in page.extract_tables():
                if done:
                    break
                for row in table:
                    if is_table2_header(row):
                        done = True
                        break
                    if is_table1_header(row):
                        continue
                    # Must have at least waterbody and town columns
                    if len(row) < 2 or not row[0] or not row[1]:
                        continue
                    rows.append(row)

    locations = []
    for row in rows:
        waterbody_cell = (row[0] or "").strip()
        towns_cell = (row[1] or "").strip()
        dates_cell = (row[2] or "").strip() if len(row) > 2 else ""

        if not waterbody_cell or not towns_cell:
            continue

        name, mgmt = parse_waterbody(waterbody_cell)
        towns = [t.strip() for t in towns_cell.split(",") if t.strip()]
        stocked_dates = parse_stocked_dates(dates_cell, year)

        locations.append({
            "waterbody": name,
            "towns": towns,
            "management_type": mgmt,
            "stocked_dates": sorted(stocked_dates),
        })

    return report_date, catch_release, locations


def build_json(report_date, catch_release, locations):
    """Build the stocking_data.json structure."""
    # Group recently stocked by date
    by_date = defaultdict(list)
    for loc in locations:
        for d in loc["stocked_dates"]:
            by_date[d].append({
                "waterbody": loc["waterbody"],
                "towns": loc["towns"],
                "management_type": loc["management_type"],
            })

    recently_stocked = [
        {"date": date, "locations": locs}
        for date, locs in sorted(by_date.items(), reverse=True)
    ]

    return {
        "report_date": report_date,
        "source": "CT DEEP Fisheries Division Spring 2026",
        "season": "Spring 2026",
        "catch_and_release_until": catch_release,
        "recently_stocked": recently_stocked,
        "all_locations": locations,
    }


def main():
    pdf_path = find_latest_pdf()
    print(f"Parsing: {pdf_path.name}")

    report_date, catch_release, locations = parse_pdf(pdf_path)
    print(f"Report date: {report_date}")
    print(f"Catch & release until: {catch_release}")
    print(f"Total locations: {len(locations)}")
    stocked = [l for l in locations if l["stocked_dates"]]
    print(f"Stocked so far: {len(stocked)}")

    data = build_json(report_date, catch_release, locations)

    with open(OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Written: {OUTPUT}")


if __name__ == "__main__":
    main()

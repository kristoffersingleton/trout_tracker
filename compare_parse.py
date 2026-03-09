#!/usr/bin/env python3
"""
Compare the Python PDF parser vs Claude API for CT trout stocking data.

For each run:
  - Downloads the current PDF from CT DEEP (if not already fetched today)
  - Runs parse_pdf.py (local Python approach)
  - Calls Claude API with the raw table text (Claude approach)
  - Compares results: location counts, stocked dates, management types
  - Appends a narrative entry to parse_history.md
  - Updates stocking_data.json with the Python parser output

Usage:
  .venv/bin/python3 compare_parse.py
  .venv/bin/python3 compare_parse.py --no-download   # use most recent PDF already in pdf/

Requires ANTHROPIC_API_KEY in environment.
"""

import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import anthropic
import pdfplumber

from parse_pdf import build_json, find_latest_pdf, parse_pdf

BASE = Path(__file__).parent
PDF_DIR = BASE / "pdf"
OUTPUT = BASE / "stocking_data.json"
HISTORY_FILE = BASE / "parse_history.md"

PDF_URL = "https://portal.ct.gov/-/media/deep/fishing/weekly_reports/currentstockingreport.pdf"

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_pdf(force=False):
    """Download the current CT DEEP stocking PDF. Returns Path to saved file."""
    today = datetime.now().strftime("%Y-%m-%d")
    dest = PDF_DIR / f"{today}-CurrentStockingReport.pdf"
    if dest.exists() and not force:
        print(f"Already have today's PDF: {dest.name}")
        return dest
    print(f"Downloading from CT DEEP...", end=" ", flush=True)
    t0 = time.time()
    urllib.request.urlretrieve(PDF_URL, dest)
    elapsed = time.time() - t0
    size_kb = dest.stat().st_size // 1024
    print(f"{size_kb} KB in {elapsed:.1f}s — saved as {dest.name}")
    return dest


# ---------------------------------------------------------------------------
# Python parser
# ---------------------------------------------------------------------------

def run_python_parser(pdf_path):
    """Run parse_pdf and return (data_dict, elapsed_seconds)."""
    t0 = time.time()
    report_date, catch_release, locations = parse_pdf(pdf_path)
    elapsed = time.time() - t0
    data = build_json(report_date, catch_release, locations)
    return data, elapsed


# ---------------------------------------------------------------------------
# Claude parser
# ---------------------------------------------------------------------------

CLAUDE_SYSTEM = """You parse CT DEEP trout stocking report tables into structured JSON.
Return only valid JSON, no prose, no markdown fences."""

CLAUDE_PROMPT = """\
Below is Table 1 from the CT DEEP Spring {year} trout stocking report.
The report date is {report_date}.

Each line has three fields separated by " | ":
  Waterbody (may include management type suffix) | Town(s) | Stocked dates

Rules:
- Split waterbody from management type on " – ", " - ", or " -" before uppercase.
  Everything before = waterbody name. Everything after = management_type (or null).
- Towns: split comma-separated string into a list.
- Stocked dates: "M/D" or "M/D, M/D" → "YYYY-MM-DD" list using the report year.
  Empty = [].

Return this exact JSON structure (no other text):
{{
  "locations": [
    {{
      "waterbody": "string",
      "management_type": "string or null",
      "towns": ["string"],
      "stocked_dates": ["YYYY-MM-DD"]
    }}
  ]
}}

Table data:
{table_text}
"""


def extract_table1_rows(pdf_path):
    """Extract Table 1 rows via pdfplumber. Returns list of [waterbody, towns, dates]."""
    rows = []
    done = False
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[1:]:
            if done:
                break
            for table in page.extract_tables():
                if done:
                    break
                for row in table:
                    if not row or not row[0]:
                        continue
                    cell = row[0].strip()
                    # Table 1 header — skip
                    if "Alphabetically" in cell:
                        continue
                    # Table 2 header — stop
                    if cell.startswith("Waterbody") and "Alphabetically" not in cell:
                        done = True
                        break
                    if len(row) >= 2 and row[1]:
                        rows.append(row)
    return rows


def run_claude_parser(pdf_path, report_date):
    """Call Claude API to parse Table 1. Returns (locations_list, elapsed_seconds)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set")

    rows = extract_table1_rows(pdf_path)
    table_text = "\n".join(
        f"{r[0]} | {r[1]} | {r[2] if len(r) > 2 and r[2] else ''}"
        for r in rows
    )
    year = report_date[:4]

    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=CLAUDE_SYSTEM,
        messages=[{
            "role": "user",
            "content": CLAUDE_PROMPT.format(
                year=year,
                report_date=report_date,
                table_text=table_text,
            ),
        }],
    )
    elapsed = time.time() - t0

    raw = message.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = "\n".join(raw.splitlines()[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.splitlines()[:-1])
    data = json.loads(raw)
    return data["locations"], elapsed


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def compare(py_data, cl_locations):
    """Return a metrics dict comparing both parsers."""
    py_map = {loc["waterbody"]: loc for loc in py_data["all_locations"]}
    cl_map = {loc["waterbody"]: loc for loc in cl_locations}

    py_names = set(py_map)
    cl_names = set(cl_map)
    common = py_names & cl_names

    date_mismatches = []
    mgmt_mismatches = []

    for name in sorted(common):
        py_loc = py_map[name]
        cl_loc = cl_map[name]
        if set(py_loc["stocked_dates"]) != set(cl_loc.get("stocked_dates") or []):
            date_mismatches.append({
                "waterbody": name,
                "python": sorted(py_loc["stocked_dates"]),
                "claude": sorted(cl_loc.get("stocked_dates") or []),
            })
        py_mgmt = py_loc.get("management_type")
        cl_mgmt = cl_loc.get("management_type")
        if py_mgmt != cl_mgmt:
            mgmt_mismatches.append({
                "waterbody": name,
                "python": py_mgmt,
                "claude": cl_mgmt,
            })

    py_stocked = sum(1 for l in py_data["all_locations"] if l["stocked_dates"])
    cl_stocked = sum(1 for l in cl_locations if l.get("stocked_dates"))
    total = max(len(py_names), len(cl_names))

    return {
        "py_total": len(py_names),
        "cl_total": len(cl_names),
        "py_stocked": py_stocked,
        "cl_stocked": cl_stocked,
        "common": len(common),
        "only_in_python": sorted(py_names - cl_names),
        "only_in_claude": sorted(cl_names - py_names),
        "date_mismatches": date_mismatches,
        "mgmt_mismatches": mgmt_mismatches,
        "agreement_pct": round(len(common) / total * 100, 1) if total else 0,
    }


def print_comparison(metrics, py_elapsed, cl_elapsed):
    """Print comparison summary to stdout."""
    print(f"\n{'='*60}")
    print(f"COMPARISON RESULTS")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'Python':>10} {'Claude':>10}")
    print(f"{'-'*30} {'-'*10} {'-'*10}")
    print(f"{'Total locations':<30} {metrics['py_total']:>10} {metrics['cl_total']:>10}")
    print(f"{'Stocked so far':<30} {metrics['py_stocked']:>10} {metrics['cl_stocked']:>10}")
    print(f"{'Time (seconds)':<30} {py_elapsed:>10.1f} {cl_elapsed:>10.1f}")
    print(f"\nLocation name agreement: {metrics['agreement_pct']}%")

    if metrics["only_in_python"]:
        print(f"\nOnly in Python ({len(metrics['only_in_python'])}):")
        for name in metrics["only_in_python"][:5]:
            print(f"  - {name}")
    if metrics["only_in_claude"]:
        print(f"\nOnly in Claude ({len(metrics['only_in_claude'])}):")
        for name in metrics["only_in_claude"][:5]:
            print(f"  - {name}")
    if metrics["date_mismatches"]:
        print(f"\nDate disagreements ({len(metrics['date_mismatches'])}):")
        for m in metrics["date_mismatches"][:5]:
            print(f"  {m['waterbody']}: py={m['python']} cl={m['claude']}")
    if metrics["mgmt_mismatches"]:
        print(f"\nManagement type disagreements ({len(metrics['mgmt_mismatches'])}):")
        for m in metrics["mgmt_mismatches"][:5]:
            print(f"  {m['waterbody']}: py={m['python']!r} cl={m['claude']!r}")

    if not any([metrics["only_in_python"], metrics["only_in_claude"],
                metrics["date_mismatches"], metrics["mgmt_mismatches"]]):
        print("\nPerfect agreement — both parsers produced identical results.")


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def verdict(metrics, py_elapsed, cl_elapsed):
    """Compose a one-sentence verdict for the history entry."""
    problems = []
    if metrics["only_in_python"]:
        problems.append(f"Claude missed {len(metrics['only_in_python'])} location(s)")
    if metrics["only_in_claude"]:
        problems.append(f"Python missed {len(metrics['only_in_claude'])} location(s)")
    if metrics["date_mismatches"]:
        n = len(metrics["date_mismatches"])
        problems.append(f"{n} stocking date disagreement{'s' if n > 1 else ''}")
    if metrics["mgmt_mismatches"]:
        n = len(metrics["mgmt_mismatches"])
        problems.append(f"{n} management type disagreement{'s' if n > 1 else ''}")

    speed_winner = "Python" if py_elapsed < cl_elapsed else "Claude"
    speed_ratio = max(py_elapsed, cl_elapsed) / max(min(py_elapsed, cl_elapsed), 0.01)

    if not problems:
        return (
            f"Both parsers agreed completely. "
            f"Python was {speed_ratio:.0f}x faster ({py_elapsed:.1f}s vs {cl_elapsed:.1f}s)."
        )
    else:
        issues = "; ".join(problems)
        return (
            f"Discrepancies: {issues}. "
            f"{speed_winner} was faster ({py_elapsed:.1f}s vs {cl_elapsed:.1f}s). "
            f"Location name agreement: {metrics['agreement_pct']}%."
        )


def append_history(run_dt, pdf_name, report_date, metrics, py_elapsed, cl_elapsed, stocking_days=0):
    """Append a narrative run entry to parse_history.md."""
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(
            "# CT Trout Stocking — Parse Comparison History\n\n"
            "Each entry records one comparison run: Python script vs Claude API.\n"
            "Goal: understand when each approach is more accurate or reliable.\n\n"
            "---\n\n"
        )

    detail_lines = []
    if metrics["only_in_python"]:
        detail_lines.append(
            f"Python-only locations: {', '.join(metrics['only_in_python'][:5])}"
            + (" ..." if len(metrics["only_in_python"]) > 5 else "")
        )
    if metrics["only_in_claude"]:
        detail_lines.append(
            f"Claude-only locations: {', '.join(metrics['only_in_claude'][:5])}"
            + (" ..." if len(metrics["only_in_claude"]) > 5 else "")
        )
    for m in metrics["date_mismatches"][:3]:
        detail_lines.append(
            f"Date mismatch — {m['waterbody']}: Python {m['python']} / Claude {m['claude']}"
        )
    for m in metrics["mgmt_mismatches"][:3]:
        detail_lines.append(
            f"Mgmt mismatch — {m['waterbody']}: Python {m['python']!r} / Claude {m['claude']!r}"
        )

    details_block = (
        "\n".join(f"  - {l}" for l in detail_lines)
        if detail_lines
        else "  - None — perfect agreement"
    )

    entry = (
        f"## {run_dt}\n\n"
        f"**PDF:** `{pdf_name}`  \n"
        f"**Report date:** {report_date}  \n"
        f"**Stocked so far:** {metrics['py_stocked']} locations across "
        f"{stocking_days} stocking day{'s' if stocking_days != 1 else ''}\n\n"
        f"| | Python | Claude |\n"
        f"|---|---|---|\n"
        f"| Total locations | {metrics['py_total']} | {metrics['cl_total']} |\n"
        f"| Stocked so far | {metrics['py_stocked']} | {metrics['cl_stocked']} |\n"
        f"| Location agreement | {metrics['agreement_pct']}% | — |\n"
        f"| Parse time | {py_elapsed:.1f}s | {cl_elapsed:.1f}s |\n\n"
        f"**Discrepancies:**\n{details_block}\n\n"
        f"**Summary:** {verdict(metrics, py_elapsed, cl_elapsed)}\n\n"
        f"---\n\n"
    )

    with open(HISTORY_FILE, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    no_download = "--no-download" in sys.argv

    if no_download:
        pdf_path = find_latest_pdf()
        print(f"Using existing PDF: {pdf_path.name}")
    else:
        pdf_path = download_pdf()

    # Python parser
    print("\nRunning Python parser...", end=" ", flush=True)
    py_data, py_elapsed = run_python_parser(pdf_path)
    report_date = py_data["report_date"]
    print(f"{len(py_data['all_locations'])} locations in {py_elapsed:.2f}s")

    # Claude parser
    print("Running Claude parser...", end=" ", flush=True)
    try:
        cl_locs, cl_elapsed = run_claude_parser(pdf_path, report_date)
        print(f"{len(cl_locs)} locations in {cl_elapsed:.1f}s")
        cl_ok = True
    except EnvironmentError as e:
        print(f"SKIPPED ({e})")
        cl_locs, cl_elapsed = [], 0.0
        cl_ok = False

    if cl_ok:
        metrics = compare(py_data, cl_locs)
        print_comparison(metrics, py_elapsed, cl_elapsed)
        run_dt = datetime.now().strftime("%Y-%m-%d %H:%M")
        stocking_days = len(py_data.get("recently_stocked", []))
        append_history(run_dt, pdf_path.name, report_date, metrics, py_elapsed, cl_elapsed, stocking_days)
        print(f"\nHistory updated: {HISTORY_FILE}")
    else:
        print("\nSkipping comparison (no Claude results).")

    # Always write stocking_data.json from the Python parse
    with open(OUTPUT, "w") as f:
        json.dump(py_data, f, indent=2)
    print(f"stocking_data.json updated (Python parse, report date {report_date})")


if __name__ == "__main__":
    main()

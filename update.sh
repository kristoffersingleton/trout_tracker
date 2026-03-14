#!/usr/bin/env bash
# Daily CT trout stocking update
# Usage: ./update.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PDF_URL="https://portal.ct.gov/-/media/DEEP/fishing/weekly_reports/CurrentStockingReport.pdf"
DATE=$(date +%Y-%m-%d)
PDF_PATH="pdf/${DATE}-CurrentStockingReport.pdf"

echo "==> Downloading stocking report..."
curl -sf -o "$PDF_PATH" "$PDF_URL"
echo "    Saved: $PDF_PATH"

echo "==> Parsing PDF..."
.venv/bin/python parse_pdf.py

echo "==> Generating HTML map..."
.venv/bin/python generate_html.py

echo "==> Committing and pushing..."
git add "$PDF_PATH" stocking_data.json docs/index.html
git commit -m "Daily update ${DATE}"
git push

echo ""
echo "Done! Live at: https://kristoffersingleton.github.io/trout_tracker/"

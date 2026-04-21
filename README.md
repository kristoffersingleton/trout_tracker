# CT Trout Stocking Finder

**[🗺️ Open the Live Map →](https://kristoffersingleton.github.io/trout_tracker/)**

Find the closest recently stocked trout fishing locations in Connecticut, updated daily from CT DEEP Fisheries Division stocking reports.

## Features

- Interactive Leaflet map with color-coded freshness markers
- Sortable table by distance, days since stocking, or tier
- Browser geolocation — distances recalculate from your actual position
- Filter by tier (Hot / Fresh / Aging / Scheduled) and distance radius
- Google Maps links for every location
- Auto-updated daily via GitHub Actions

## Recency Tiers

| Tier | Days Since Stocking | Meaning |
|------|--------------------:|---------|
| 🔥 Hot | 0–2 days | Just stocked, best chance |
| ✓ Fresh | 3–5 days | Still good |
| ⏳ Aging | 6+ days | May be fished out |
| — Scheduled | not yet | On the list, not stocked yet |

## Local Scripts

```bash
python3 map_stocked.py      # Compact view with Google Maps links
python3 find_stocked.py     # Detailed table with distance and tier
python3 generate_kml.py     # Creates trout_stocking.kml for Google Maps import
python3 generate_html.py    # Regenerates docs/index.html
```

## Updating Stocking Data

Data updates automatically each morning via GitHub Actions. To update manually:

```bash
DATE=$(date +%Y-%m-%d)
curl -o "pdf/${DATE}-CurrentStockingReport.pdf" \
  "https://portal.ct.gov/-/media/DEEP/fishing/weekly_reports/CurrentStockingReport.pdf"
python3 parse_pdf.py
python3 generate_html.py
```

## Configuration

Home location defaults to Redding, CT. Edit `HOME_LOCATION` in `config.py`:

```python
HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
```

## Project Structure

| File | Description |
|------|-------------|
| `parse_pdf.py` | Parses CT DEEP PDF → `stocking_data.json` |
| `generate_html.py` | Builds `docs/index.html` (the live map) |
| `generate_kml.py` | Generates KML for Google Maps/Earth import |
| `find_stocked.py` | CLI: detailed table with distance and tier |
| `map_stocked.py` | CLI: compact view with Google Maps links |
| `stocking_data.json` | Parsed stocking data with dates and locations |
| `ct_town_coords.json` | Coordinates for 120+ Connecticut towns |
| `pdf/` | Downloaded CT DEEP stocking report PDFs |
| `docs/` | Generated static site (served via GitHub Pages) |

## Management Type Abbreviations

| Code | Meaning |
|------|---------|
| TML | Trout Management Lake — 1 trout/day limit |
| TMA | Trout Management Area — special regulations |
| TTA | Trophy Trout Area — larger fish, special regs |
| TP | Trout Park — family-friendly |
| CFW | Community Fishing Waters — urban/accessible |

## Data Source

[CT DEEP Fisheries Division](https://portal.ct.gov/DEEP/Fishing) Spring 2026 Stocking Reports  
Follow [@ctfishandwildlife](https://www.instagram.com/ctfishandwildlife) for updates

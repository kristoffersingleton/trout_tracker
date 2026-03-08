# CT Trout Stocking Finder

Find the closest recently stocked trout fishing locations in Connecticut based on CT DEEP Fisheries Division stocking reports.

## How It Works

```
CT DEEP PDF Report
      │
      ▼
 stocking_data.json  ◄──  ct_town_coords.json
      │                         │
      │    (haversine distance)  │
      ▼                         ▼
 find_stocked.py ──────── town coordinates
      │
      ├──► find_stocked.sh   (prints + copies to clipboard)
      │
 map_stocked.py  ──────── Google Maps URLs
      │
      ├── compact view (default)
      ├── --md   markdown table
      └── --links  links only

 generate_kml.py ──────── trout_stocking.kml
                               │
                               ▼
                       Google My Maps import
                    (green/blue/orange/yellow pins)
```

## Quick Start

```bash
# Show closest stocked locations + copy to clipboard (WSL2)
./find_stocked.sh

# Compact view with Google Maps links
python3 map_stocked.py

# Detailed view sorted by distance
python3 find_stocked.py

# All recently stocked locations by date
python3 find_stocked.py --all

# Search locations near a specific town
python3 find_stocked.py --town Danbury
```

## Sample Output

```
======================================================================
CLOSEST RECENTLY STOCKED LOCATIONS
From: Redding, CT  |  Report Date: 2026-03-05
🔥 Hot (0-2d)  ✓ Fresh (3-5d)  ⏳ Aging (6+d)
======================================================================

   Waterbody                        Town              Miles   Days  Tier
   -------------------------------- ---------------- ------  ----  -----
🔥  Ball Pond                        New Fairfield     12.4     0d  HOT
✓   Squantz Pond [TML]               New Fairfield     16.1     1d  FRESH
⏳  Quonnipaug Lake [TML]            Guilford          36.4     6d  AGING

* Catch & Release until April 11, 2026 at 6:00 AM
* TML = Trout Management Lake (1 trout/day limit)
```

## Recency Tiers

| Symbol | Tier | Days Since Stocking | Meaning |
|--------|------|--------------------:|---------|
| 🔥 | Hot | 0–2 days | Just stocked, best chance |
| ✓ | Fresh | 3–5 days | Still good |
| ⏳ | Aging | 6+ days | May be fished out |

## Scripts

| File | Description |
|------|-------------|
| `find_stocked.sh` | Runs `find_stocked.py`, displays output, and copies to clipboard |
| `find_stocked.py` | Detailed table with distance, days, and recency tier |
| `map_stocked.py` | Compact view with Google Maps links |
| `generate_kml.py` | Generates `trout_stocking.kml` for Google Maps/Earth import |

## Data Files

| File | Description |
|------|-------------|
| `stocking_data.json` | Parsed stocking data with dates and locations |
| `ct_town_coords.json` | Coordinates for 120+ Connecticut towns |
| `trout_stocking.kml` | Generated KML for map import |
| `pdf/` | Directory for downloaded CT DEEP stocking report PDFs |

## Configuration

Edit `HOME_LOCATION` at the top of any script to change your home location:

```python
HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
```

## map_stocked.py Options

```bash
python3 map_stocked.py           # Compact view with map links
python3 map_stocked.py --md      # Markdown table (for notes/docs)
python3 map_stocked.py --links   # Links only (minimal)
```

## Google Maps / KML Integration

Generate a KML file to import all locations into Google My Maps:

```bash
python3 generate_kml.py
# Creates trout_stocking.kml
```

KML pin colors:
- **Green** - Hot (0–2 days)
- **Blue** - Fresh (3–5 days)
- **Orange** - Aging (6+ days)
- **Yellow** - Scheduled, not yet stocked
- **Red star** - Your home location

Import steps:
1. Go to [Google My Maps](https://www.google.com/maps/d/)
2. Create new map → Import → Select `trout_stocking.kml`
3. Save to access from the Google Maps app on your phone

## Updating Stocking Data

1. Download the latest stocking report PDF from [CT DEEP Fisheries](https://portal.ct.gov/DEEP/Fishing/Freshwater/Freshwater-Fishing)
2. Save it to the `pdf/` directory
3. Parse the PDF to update `stocking_data.json`

## Management Type Abbreviations

| Code | Meaning | Notes |
|------|---------|-------|
| TML | Trout Management Lake | 1 trout/day limit |
| TMA | Trout Management Area | Special regulations apply |
| TTA | Trophy Trout Area | Larger fish, special regs |
| TP | Trout Park | Family-friendly locations |
| WTMA | Wild Trout Management Area | Catch and release encouraged |
| CFW | Community Fishing Waters | Urban/accessible locations |

## Regulations Reminder

- **Catch and Release Season**: March 1 – April 11 (6:00 AM)
- All trout must be released without avoidable injury during this period
- Exceptions: TML (1/day), Sea Run streams (2/day, 15" min), Tidal Waters

## Data Source

CT DEEP Fisheries Division Spring 2026 Stocking Reports.

- Website: [CT DEEP Fishing](https://portal.ct.gov/DEEP/Fishing)
- Facebook: [CTFishandWildlife](https://www.facebook.com/CTFishandWildlife)
- Instagram: [@ctfishandwildlife](https://www.instagram.com/ctfishandwildlife)
- Interactive Map: [CT DEEP Stocking Map](https://portal.ct.gov/DEEP/Fishing/Freshwater/Trout-Stocking-Report)

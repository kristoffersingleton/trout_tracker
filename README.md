# CT Trout Stocking Finder

Find the closest recently stocked trout fishing locations in Connecticut based on CT DEEP Fisheries Division stocking reports.

## Quick Start

```bash
# Show closest stocked locations with Google Maps links
python3 map_stocked.py

# Detailed view of closest locations
python3 find_stocked.py

# Show all recently stocked locations by date
python3 find_stocked.py --all

# Search locations near a specific town
python3 find_stocked.py --town Danbury
```

## Sample Output

```
Stocked Locations from Redding (as of 2026-03-05)

 12.4mi  Ball Pond - New Fairfield (03-05)
        https://www.google.com/maps/search/Ball+Pond,+CT/@41.4665,-73.4851,14z

 16.1mi  Squantz Pond [TML] - New Fairfield (03-04)
        https://www.google.com/maps/search/Squantz+Pond,+CT/@41.52205,-73.49135,14z

 36.4mi  Quonnipaug Lake [TML] - Guilford (03-02)
        https://www.google.com/maps/search/Quonnipaug+Lake,+CT/@41.2887,-72.6815,14z
```

## Configuration

Edit `find_stocked.py` to change your home location:

```python
HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
```

## Files

| File | Description |
|------|-------------|
| `map_stocked.py` | Compact view with Google Maps links |
| `find_stocked.py` | Detailed query tool with distance calculations |
| `generate_kml.py` | Generate KML file for Google Maps/Earth |
| `stocking_data.json` | Parsed stocking data with dates and locations |
| `ct_town_coords.json` | Coordinates for 120+ Connecticut towns |
| `pdf/` | Directory for downloaded CT DEEP stocking report PDFs |

## map_stocked.py Options

```bash
python3 map_stocked.py           # Compact view with map links
python3 map_stocked.py --md      # Markdown table (for notes/docs)
python3 map_stocked.py --links   # Just links (minimal)
```

## Google Maps Integration

Generate a KML file to import all locations into Google My Maps:

```bash
python3 generate_kml.py
```

This creates `trout_stocking.kml` with all locations within 100 miles of your home:
- **Green pins** - Already stocked this season
- **Yellow pins** - Scheduled but not yet stocked
- **Red star** - Your home location

To import:
1. Go to [Google My Maps](https://www.google.com/maps/d/)
2. Create new map → Import → Select `trout_stocking.kml`
3. Save to access from Google Maps app on your phone

## Updating Data

1. Download the latest stocking report PDF from [CT DEEP Fisheries](https://portal.ct.gov/DEEP/Fishing/Freshwater/Freshwater-Fishing)
2. Save it to the `pdf/` directory
3. Parse the new PDF to update `stocking_data.json`

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

- **Catch and Release Season**: March 1 - April 11 (6:00 AM)
- All trout must be released without avoidable injury during this period
- Exceptions: TML (1/day), Sea Run streams (2/day, 15" min), Tidal Waters

## Data Source

Data sourced from CT DEEP Fisheries Division Spring 2026 Stocking Reports.

- Website: [CT DEEP Fishing](https://portal.ct.gov/DEEP/Fishing)
- Facebook: [CTFishandWildlife](https://www.facebook.com/CTFishandWildlife)
- Instagram: [@ctfishandwildlife](https://www.instagram.com/ctfishandwildlife)
- Interactive Map: [CT DEEP Stocking Map](https://portal.ct.gov/DEEP/Fishing/Freshwater/Trout-Stocking-Report)

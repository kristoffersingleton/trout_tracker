# CT Trout Stocking Finder

Tools to find the closest recently stocked trout fishing locations in Connecticut based on CT DEEP Fisheries Division stocking reports.

## Project Structure

- `find_stocked.py` - Detailed query tool with distance calculations
- `map_stocked.py` - Compact view with Google Maps links  
- `generate_kml.py` - Generate KML for Google Maps/Earth import
- `stocking_data.json` - Parsed stocking data with dates and locations
- `ct_town_coords.json` - Coordinates for 120+ CT towns
- `pdf/` - Directory for downloaded CT DEEP stocking report PDFs

## Configuration

Home location is set to Redding, CT. Edit the `HOME_LOCATION` variable at the top of any script to change:

```python
HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
```

## Common Tasks

### Show closest stocked locations
```bash
python3 map_stocked.py      # Compact with map links
python3 find_stocked.py     # Detailed view
```

### Generate KML for Google Maps
```bash
python3 generate_kml.py     # Creates trout_stocking.kml
```

### Update stocking data
1. Download new PDF from CT DEEP to `pdf/` directory
2. Parse PDF to update `stocking_data.json` (manually or with Claude)

## Data Source

CT DEEP Fisheries Division Spring 2026 Stocking Reports

#!/usr/bin/env python3
"""
Generate KML file of CT trout stocking locations for Google Maps/Earth.
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
MAX_DISTANCE_MILES = 100

# Recency tiers (days since stocking)
TIER_HOT = 2      # 0-2 days: Hot - just stocked
TIER_FRESH = 5    # 3-5 days: Fresh - still good
# 6+ days: Aging - may be fished out

def load_data():
    data_file = Path(__file__).parent / "stocking_data.json"
    with open(data_file) as f:
        return json.load(f)

def load_town_coords():
    coords_file = Path(__file__).parent / "ct_town_coords.json"
    with open(coords_file) as f:
        return json.load(f)

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3959
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def get_location_coords(towns, town_coords):
    lats, lons = [], []
    for town in towns:
        town_clean = town.strip()
        if town_clean in town_coords:
            lats.append(town_coords[town_clean]["lat"])
            lons.append(town_coords[town_clean]["lon"])
        elif town_clean == "E Granby":
            lats.append(town_coords["East Granby"]["lat"])
            lons.append(town_coords["East Granby"]["lon"])
    if lats and lons:
        return sum(lats) / len(lats), sum(lons) / len(lons)
    return None, None

def escape_xml(text):
    """Escape special XML characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("'", "&apos;")
            .replace('"', "&quot;"))

def get_recency_tier(stocked_dates, report_date):
    """
    Determine recency tier based on most recent stocking date.
    Returns: 'hot', 'fresh', 'aging', or 'scheduled'
    """
    if not stocked_dates:
        return 'scheduled'

    report_dt = datetime.strptime(report_date, "%Y-%m-%d")
    most_recent = max(datetime.strptime(d, "%Y-%m-%d") for d in stocked_dates)
    days_ago = (report_dt - most_recent).days

    if days_ago <= TIER_HOT:
        return 'hot'
    elif days_ago <= TIER_FRESH:
        return 'fresh'
    else:
        return 'aging'

def get_days_since(stocked_dates, report_date):
    """Get days since most recent stocking."""
    if not stocked_dates:
        return None
    report_dt = datetime.strptime(report_date, "%Y-%m-%d")
    most_recent = max(datetime.strptime(d, "%Y-%m-%d") for d in stocked_dates)
    return (report_dt - most_recent).days

def generate_kml():
    data = load_data()
    town_coords = load_town_coords()
    report_date = data["report_date"]

    locations = []

    for loc in data["all_locations"]:
        lat, lon = get_location_coords(loc["towns"], town_coords)
        if lat and lon:
            distance = haversine_distance(HOME_LOCATION["lat"], HOME_LOCATION["lon"], lat, lon)
            if distance <= MAX_DISTANCE_MILES:
                stocked_dates = loc.get("stocked_dates", [])
                tier = get_recency_tier(stocked_dates, report_date)
                days_ago = get_days_since(stocked_dates, report_date)

                locations.append({
                    "waterbody": loc["waterbody"],
                    "towns": loc["towns"],
                    "management_type": loc.get("management_type"),
                    "stocked_dates": stocked_dates,
                    "tier": tier,
                    "days_ago": days_ago,
                    "distance": round(distance, 1),
                    "lat": lat,
                    "lon": lon
                })

    # Sort by distance
    locations.sort(key=lambda x: x["distance"])

    # Generate KML
    kml = []
    kml.append('<?xml version="1.0" encoding="UTF-8"?>')
    kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    kml.append('<Document>')
    kml.append(f'  <name>CT Trout Stocking - {MAX_DISTANCE_MILES}mi from {HOME_LOCATION["name"]}</name>')
    kml.append(f'  <description>Trout stocking locations within {MAX_DISTANCE_MILES} miles of {HOME_LOCATION["name"]}, CT. Report date: {report_date}</description>')

    # Define styles for each tier
    kml.append('''  <Style id="hot">
    <IconStyle>
      <scale>1.3</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="fresh">
    <IconStyle>
      <scale>1.1</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="aging">
    <IconStyle>
      <scale>1.0</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/orange-circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="scheduled">
    <IconStyle>
      <scale>0.9</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="home">
    <IconStyle>
      <scale>1.4</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-stars.png</href></Icon>
    </IconStyle>
  </Style>''')

    # Add home marker
    kml.append('  <Placemark>')
    kml.append(f'    <name>HOME - {HOME_LOCATION["name"]}</name>')
    kml.append('    <styleUrl>#home</styleUrl>')
    kml.append(f'    <Point><coordinates>{HOME_LOCATION["lon"]},{HOME_LOCATION["lat"]},0</coordinates></Point>')
    kml.append('  </Placemark>')

    # Group by tier
    tiers = {
        'hot': {'name': 'Hot - Just Stocked (0-2 days)', 'locations': []},
        'fresh': {'name': 'Fresh (3-5 days)', 'locations': []},
        'aging': {'name': 'Aging - May Be Fished Out (6+ days)', 'locations': []},
        'scheduled': {'name': 'Scheduled - Not Yet Stocked', 'locations': []}
    }

    for loc in locations:
        tiers[loc['tier']]['locations'].append(loc)

    # Add folders for each tier
    for tier_key in ['hot', 'fresh', 'aging', 'scheduled']:
        tier = tiers[tier_key]
        if not tier['locations']:
            continue

        kml.append(f'  <Folder>')
        kml.append(f'    <name>{tier["name"]} ({len(tier["locations"])})</name>')

        for loc in tier['locations']:
            name = escape_xml(loc["waterbody"])
            towns = escape_xml(", ".join(loc["towns"]))
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""

            if loc["stocked_dates"]:
                dates = ", ".join(loc["stocked_dates"])
                days_str = f" ({loc['days_ago']}d ago)" if loc['days_ago'] is not None else ""
                status = f"Stocked: {dates}{days_str}"
            else:
                status = "Not yet stocked"

            desc = f"Towns: {towns}\n{status}\nDistance: {loc['distance']} mi{mgmt}"

            kml.append('    <Placemark>')
            kml.append(f'      <name>{name}</name>')
            kml.append(f'      <description>{escape_xml(desc)}</description>')
            kml.append(f'      <styleUrl>#{tier_key}</styleUrl>')
            kml.append(f'      <Point><coordinates>{loc["lon"]},{loc["lat"]},0</coordinates></Point>')
            kml.append('    </Placemark>')

        kml.append('  </Folder>')

    kml.append('</Document>')
    kml.append('</kml>')

    return "\n".join(kml), locations, tiers

def main():
    kml_content, locations, tiers = generate_kml()

    output_file = Path(__file__).parent / "trout_stocking.kml"
    with open(output_file, "w") as f:
        f.write(kml_content)

    print(f"Generated: {output_file}")
    print(f"Locations within {MAX_DISTANCE_MILES} miles of {HOME_LOCATION['name']}:\n")
    print(f"  {'Hot (0-2 days):':<30} {len(tiers['hot']['locations']):>3}  (green)")
    print(f"  {'Fresh (3-5 days):':<30} {len(tiers['fresh']['locations']):>3}  (blue)")
    print(f"  {'Aging (6+ days):':<30} {len(tiers['aging']['locations']):>3}  (orange)")
    print(f"  {'Scheduled:':<30} {len(tiers['scheduled']['locations']):>3}  (yellow)")
    print(f"  {'-'*38}")
    print(f"  {'Total:':<30} {len(locations):>3}")
    print()
    print("To use:")
    print("  1. Go to https://www.google.com/maps/d/")
    print("  2. Create new map → Import → Select trout_stocking.kml")
    print("  3. Save & access from Google Maps app on your phone")

if __name__ == "__main__":
    main()

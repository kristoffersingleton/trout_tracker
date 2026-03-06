#!/usr/bin/env python3
"""
Generate KML file of CT trout stocking locations for Google Maps/Earth.
"""

import json
import math
from pathlib import Path

HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}
MAX_DISTANCE_MILES = 100

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

def generate_kml():
    data = load_data()
    town_coords = load_town_coords()

    locations = []

    for loc in data["all_locations"]:
        lat, lon = get_location_coords(loc["towns"], town_coords)
        if lat and lon:
            distance = haversine_distance(HOME_LOCATION["lat"], HOME_LOCATION["lon"], lat, lon)
            if distance <= MAX_DISTANCE_MILES:
                stocked_dates = loc.get("stocked_dates", [])
                locations.append({
                    "waterbody": loc["waterbody"],
                    "towns": loc["towns"],
                    "management_type": loc.get("management_type"),
                    "stocked_dates": stocked_dates,
                    "is_stocked": len(stocked_dates) > 0,
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
    kml.append(f'  <description>Trout stocking locations within {MAX_DISTANCE_MILES} miles of {HOME_LOCATION["name"]}, CT. Report date: {data["report_date"]}</description>')

    # Define styles
    kml.append('''  <Style id="stocked">
    <IconStyle>
      <color>ff00ff00</color>
      <scale>1.2</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="scheduled">
    <IconStyle>
      <color>ff0080ff</color>
      <scale>1.0</scale>
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

    # Add stocked locations folder
    kml.append('  <Folder>')
    kml.append('    <name>Stocked (Green)</name>')
    for loc in locations:
        if loc["is_stocked"]:
            name = escape_xml(loc["waterbody"])
            towns = escape_xml(", ".join(loc["towns"]))
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""
            dates = ", ".join(loc["stocked_dates"])
            desc = f"Towns: {towns}\nStocked: {dates}\nDistance: {loc['distance']} mi{mgmt}"

            kml.append('    <Placemark>')
            kml.append(f'      <name>{name}</name>')
            kml.append(f'      <description>{escape_xml(desc)}</description>')
            kml.append('      <styleUrl>#stocked</styleUrl>')
            kml.append(f'      <Point><coordinates>{loc["lon"]},{loc["lat"]},0</coordinates></Point>')
            kml.append('    </Placemark>')
    kml.append('  </Folder>')

    # Add scheduled locations folder
    kml.append('  <Folder>')
    kml.append('    <name>Scheduled (Yellow)</name>')
    for loc in locations:
        if not loc["is_stocked"]:
            name = escape_xml(loc["waterbody"])
            towns = escape_xml(", ".join(loc["towns"]))
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""
            desc = f"Towns: {towns}\nNot yet stocked\nDistance: {loc['distance']} mi{mgmt}"

            kml.append('    <Placemark>')
            kml.append(f'      <name>{name}</name>')
            kml.append(f'      <description>{escape_xml(desc)}</description>')
            kml.append('      <styleUrl>#scheduled</styleUrl>')
            kml.append(f'      <Point><coordinates>{loc["lon"]},{loc["lat"]},0</coordinates></Point>')
            kml.append('    </Placemark>')
    kml.append('  </Folder>')

    kml.append('</Document>')
    kml.append('</kml>')

    return "\n".join(kml), locations

def main():
    kml_content, locations = generate_kml()

    output_file = Path(__file__).parent / "trout_stocking.kml"
    with open(output_file, "w") as f:
        f.write(kml_content)

    stocked = sum(1 for loc in locations if loc["is_stocked"])
    scheduled = len(locations) - stocked

    print(f"Generated: {output_file}")
    print(f"Locations within {MAX_DISTANCE_MILES} miles of {HOME_LOCATION['name']}:")
    print(f"  - Stocked (green):   {stocked}")
    print(f"  - Scheduled (yellow): {scheduled}")
    print(f"  - Total:              {len(locations)}")
    print()
    print("To use:")
    print("  1. Go to https://www.google.com/maps/d/")
    print("  2. Create new map → Import → Select trout_stocking.kml")
    print("  3. Save & access from Google Maps app on your phone")

if __name__ == "__main__":
    main()

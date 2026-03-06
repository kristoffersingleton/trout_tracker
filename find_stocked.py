#!/usr/bin/env python3
"""
CT DEEP Trout Stocking Finder

Query recently stocked fishing locations in Connecticut.
Find the closest stocked locations to your home.
Data sourced from CT DEEP Fisheries Division stocking reports.
"""

import json
import math
from datetime import datetime
from pathlib import Path

# Default home location - Redding, CT
HOME_LOCATION = {"lat": 41.3034, "lon": -73.3832, "name": "Redding"}

def load_data():
    """Load stocking data from JSON file."""
    data_file = Path(__file__).parent / "stocking_data.json"
    with open(data_file) as f:
        return json.load(f)

def load_town_coords():
    """Load town coordinates."""
    coords_file = Path(__file__).parent / "ct_town_coords.json"
    with open(coords_file) as f:
        return json.load(f)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula.
    Returns distance in miles.
    """
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

def get_location_coords(towns, town_coords):
    """
    Get approximate coordinates for a location based on its towns.
    Uses the centroid of all associated towns.
    """
    lats = []
    lons = []

    for town in towns:
        # Handle variations in town names
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

def get_recently_stocked_with_distance(home_lat=None, home_lon=None):
    """Get recently stocked locations with distances from home."""
    if home_lat is None:
        home_lat = HOME_LOCATION["lat"]
    if home_lon is None:
        home_lon = HOME_LOCATION["lon"]

    data = load_data()
    town_coords = load_town_coords()

    results = []

    for day in data["recently_stocked"]:
        date = day["date"]
        for loc in day["locations"]:
            lat, lon = get_location_coords(loc["towns"], town_coords)
            if lat and lon:
                distance = haversine_distance(home_lat, home_lon, lat, lon)
                results.append({
                    "waterbody": loc["waterbody"],
                    "towns": loc["towns"],
                    "management_type": loc.get("management_type"),
                    "date": date,
                    "distance_miles": round(distance, 1),
                    "lat": lat,
                    "lon": lon
                })

    # Sort by distance
    results.sort(key=lambda x: x["distance_miles"])
    return results

def print_closest_stocked(limit=15, home_lat=None, home_lon=None, home_name=None):
    """Print the closest recently stocked locations."""
    if home_name is None:
        home_name = HOME_LOCATION["name"]

    results = get_recently_stocked_with_distance(home_lat, home_lon)
    data = load_data()

    print(f"\n{'='*65}")
    print(f"CLOSEST RECENTLY STOCKED LOCATIONS")
    print(f"From: {home_name}, CT")
    print(f"Report Date: {data['report_date']}")
    print(f"{'='*65}")
    print(f"\n{'Waterbody':<35} {'Town':<18} {'Miles':>6}  {'Date'}")
    print(f"{'-'*35} {'-'*18} {'-'*6}  {'-'*10}")

    for loc in results[:limit]:
        waterbody = loc["waterbody"][:34]
        town = loc["towns"][0][:17]
        dist = loc["distance_miles"]
        date = loc["date"][5:]  # Just MM-DD
        mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""

        print(f"{waterbody:<35} {town:<18} {dist:>5.1f}   {date}{mgmt}")

    print(f"\n* Catch & Release until April 11, 2026 at 6:00 AM")
    print(f"* TML = Trout Management Lake (1 trout/day limit)")

def print_recent_stockings():
    """Print a summary of recently stocked locations."""
    data = load_data()

    print(f"\n{'='*60}")
    print(f"CT DEEP Trout Stocking Report - as of {data['report_date']}")
    print(f"{'='*60}")
    print(f"\nCatch & Release until: {data['catch_and_release_until'][:10]} at 6:00 AM")
    print(f"\n{'='*60}")
    print("RECENTLY STOCKED LOCATIONS (Most Recent First)")
    print(f"{'='*60}\n")

    for day in data["recently_stocked"]:
        date = day["date"]
        locations = day["locations"]
        print(f"\n--- {date} ({len(locations)} locations) ---\n")

        for loc in locations:
            waterbody = loc["waterbody"]
            towns = ", ".join(loc["towns"])
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""
            print(f"  {waterbody}{mgmt}")
            print(f"    Towns: {towns}")
        print()

def search_by_town(town_name):
    """Search for stocking locations in or near a specific town."""
    data = load_data()
    town_lower = town_name.lower()

    matches = []
    for loc in data["all_locations"]:
        for town in loc["towns"]:
            if town_lower in town.lower():
                matches.append(loc)
                break

    # Sort by most recently stocked first
    def sort_key(loc):
        dates = loc.get("stocked_dates", [])
        if dates:
            return max(dates)
        return "0000-00-00"

    matches.sort(key=sort_key, reverse=True)
    return matches

def print_town_search(town_name):
    """Print stocking locations for a specific town."""
    matches = search_by_town(town_name)
    town_coords = load_town_coords()

    if not matches:
        print(f"\nNo stocking locations found for '{town_name}'")
        return

    print(f"\n{'='*60}")
    print(f"Stocking Locations near {town_name}")
    print(f"{'='*60}\n")

    stocked = [m for m in matches if m.get("stocked_dates")]
    not_stocked = [m for m in matches if not m.get("stocked_dates")]

    if stocked:
        print("ALREADY STOCKED THIS SEASON:")
        print("-" * 40)
        for loc in stocked:
            waterbody = loc["waterbody"]
            towns = ", ".join(loc["towns"])
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""
            dates = ", ".join(loc["stocked_dates"])

            # Calculate distance from home
            lat, lon = get_location_coords(loc["towns"], town_coords)
            if lat and lon:
                dist = haversine_distance(HOME_LOCATION["lat"], HOME_LOCATION["lon"], lat, lon)
                dist_str = f" ({dist:.1f} mi from {HOME_LOCATION['name']})"
            else:
                dist_str = ""

            print(f"  {waterbody}{mgmt}{dist_str}")
            print(f"    Towns: {towns}")
            print(f"    Stocked: {dates}")
            print()

    if not_stocked:
        print("\nSCHEDULED (not yet stocked):")
        print("-" * 40)
        for loc in not_stocked[:10]:  # Limit to 10
            waterbody = loc["waterbody"]
            towns = ", ".join(loc["towns"])
            mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""
            print(f"  {waterbody}{mgmt}")
            print(f"    Towns: {towns}")
            print()
        if len(not_stocked) > 10:
            print(f"  ... and {len(not_stocked) - 10} more scheduled locations")

def print_help():
    """Print usage help."""
    print(f"""
CT DEEP Trout Stocking Finder
=============================

Usage:
  python find_stocked.py              Show closest stocked locations (from {HOME_LOCATION['name']})
  python find_stocked.py --all        Show all recently stocked by date
  python find_stocked.py --town NAME  Search locations near a specific town
  python find_stocked.py --help       Show this help message

Examples:
  python find_stocked.py
  python find_stocked.py --all
  python find_stocked.py --town Manchester
  python find_stocked.py --town "New Hartford"

Home location: {HOME_LOCATION['name']}, CT ({HOME_LOCATION['lat']}, {HOME_LOCATION['lon']})
To change home location, edit HOME_LOCATION in find_stocked.py
""")

def main():
    import sys

    if len(sys.argv) == 1:
        # Default: show closest stocked locations
        print_closest_stocked(limit=20)
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print_help()
    elif sys.argv[1] == "--all":
        print_recent_stockings()
    elif sys.argv[1] == "--town" and len(sys.argv) > 2:
        town = " ".join(sys.argv[2:])
        print_town_search(town)
    else:
        # Treat argument as town name for backwards compatibility
        town = " ".join(sys.argv[1:])
        if town.startswith("--"):
            print_help()
        else:
            print_town_search(town)

if __name__ == "__main__":
    main()

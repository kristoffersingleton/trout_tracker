#!/usr/bin/env python3
"""
CT Trout Stocking Map Links

Compact view of recently stocked locations with Google Maps links.
Shows recency tiers: Hot (0-2d), Fresh (3-5d), Aging (6+d)
"""

import json
import math
from datetime import datetime
from pathlib import Path

from config import HOME_LOCATION

# Recency tiers (days since stocking)
TIER_HOT = 2      # 0-2 days: Hot - just stocked
TIER_FRESH = 5    # 3-5 days: Fresh - still good

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

def google_maps_url(lat, lon, label=None):
    """Generate Google Maps URL for coordinates."""
    if label:
        query = f"{label}, CT"
        return f"https://www.google.com/maps/search/{query.replace(' ', '+')}/@{lat},{lon},14z"
    return f"https://www.google.com/maps?q={lat},{lon}"

def get_recency_tier(stocked_date, report_date):
    """Determine recency tier based on stocking date."""
    report_dt = datetime.strptime(report_date, "%Y-%m-%d")
    stock_dt = datetime.strptime(stocked_date, "%Y-%m-%d")
    days_ago = (report_dt - stock_dt).days

    if days_ago <= TIER_HOT:
        return 'hot', days_ago
    elif days_ago <= TIER_FRESH:
        return 'fresh', days_ago
    else:
        return 'aging', days_ago

def get_tier_symbol(tier):
    """Get display symbol for tier."""
    symbols = {
        'hot': '🔥',
        'fresh': '✓',
        'aging': '⏳'
    }
    return symbols.get(tier, '')

def get_stocked_with_maps():
    data = load_data()
    town_coords = load_town_coords()
    report_date = data["report_date"]
    results = []

    for day in data["recently_stocked"]:
        date = day["date"]
        tier, days_ago = get_recency_tier(date, report_date)
        for loc in day["locations"]:
            lat, lon = get_location_coords(loc["towns"], town_coords)
            if lat and lon:
                distance = haversine_distance(HOME_LOCATION["lat"], HOME_LOCATION["lon"], lat, lon)
                results.append({
                    "waterbody": loc["waterbody"],
                    "town": loc["towns"][0],
                    "management_type": loc.get("management_type"),
                    "date": date,
                    "tier": tier,
                    "days_ago": days_ago,
                    "distance": round(distance, 1),
                    "lat": lat,
                    "lon": lon,
                    "map_url": google_maps_url(lat, lon, loc["waterbody"])
                })

    results.sort(key=lambda x: x["distance"])
    return results, report_date

def print_compact(limit=15):
    results, report_date = get_stocked_with_maps()

    print(f"\nStocked Locations from {HOME_LOCATION['name']} (as of {report_date})")
    print(f"🔥 Hot (0-2d)  ✓ Fresh (3-5d)  ⏳ Aging (6+d)\n")

    for loc in results[:limit]:
        name = loc["waterbody"]
        town = loc["town"]
        dist = loc["distance"]
        days = loc["days_ago"]
        tier_sym = get_tier_symbol(loc["tier"])
        mgmt = f" [{loc['management_type']}]" if loc.get("management_type") else ""

        print(f"{tier_sym} {dist:>5.1f}mi  {name}{mgmt} - {town} ({days}d ago)")
        print(f"         {loc['map_url']}")
        print()

    print("* Catch & Release until April 11, 2026")

def print_markdown(limit=15):
    results, report_date = get_stocked_with_maps()

    print(f"\n## Stocked Locations from {HOME_LOCATION['name']}\n")
    print(f"*Updated: {report_date}* | 🔥 Hot (0-2d) | ✓ Fresh (3-5d) | ⏳ Aging (6+d)\n")
    print("| | Miles | Location | Town | Days | Map |")
    print("|---|------:|----------|------|-----:|-----|")

    for loc in results[:limit]:
        name = loc["waterbody"]
        if loc.get("management_type"):
            name += f" [{loc['management_type']}]"
        town = loc["town"]
        dist = loc["distance"]
        days = loc["days_ago"]
        tier_sym = get_tier_symbol(loc["tier"])

        print(f"| {tier_sym} | {dist:.1f} | {name} | {town} | {days} | [Map]({loc['map_url']}) |")

    print("\n*Catch & Release until April 11, 2026*")

def print_links_only(limit=10):
    results, _ = get_stocked_with_maps()

    print(f"\nTop {limit} closest stocked locations:\n")

    for i, loc in enumerate(results[:limit], 1):
        name = loc["waterbody"]
        dist = loc["distance"]
        days = loc["days_ago"]
        tier_sym = get_tier_symbol(loc["tier"])
        print(f"{i}. {tier_sym} {name} ({dist:.1f}mi, {days}d): {loc['map_url']}")

def main():
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--md" or sys.argv[1] == "--markdown":
            print_markdown(limit=20)
        elif sys.argv[1] == "--links":
            print_links_only(limit=10)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
CT Trout Stocking Map Links

Usage:
  python map_stocked.py           Compact view with map links
  python map_stocked.py --md      Markdown table format
  python map_stocked.py --links   Links only (minimal)
  python map_stocked.py --help    Show this help

Recency Tiers:
  🔥 Hot    (0-2 days)  - Just stocked, best chance
  ✓  Fresh  (3-5 days)  - Still good
  ⏳ Aging  (6+ days)   - May be fished out
""")
        else:
            print_compact(limit=20)
    else:
        print_compact(limit=20)

if __name__ == "__main__":
    main()

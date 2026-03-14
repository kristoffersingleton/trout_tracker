#!/usr/bin/env python3
"""
Generate mobile-friendly HTML map of CT trout stocking locations.
Outputs html/index.html with a Leaflet map and sortable distance table.
"""

import json
import math
from datetime import datetime
from pathlib import Path

from config import HOME_LOCATION

BASE = Path(__file__).parent
OUTPUT = BASE / "html" / "index.html"

TIER_HOT = 2
TIER_FRESH = 5

TIER_COLOR = {
    "hot":       "#22c55e",   # green
    "fresh":     "#3b82f6",   # blue
    "aging":     "#f97316",   # orange
    "scheduled": "#a3a3a3",   # gray
}

TIER_LABEL = {
    "hot":       "🔥 Hot",
    "fresh":     "✓ Fresh",
    "aging":     "⏳ Aging",
    "scheduled": "— Scheduled",
}


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3959
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_location_coords(towns, town_coords):
    lats, lons = [], []
    for town in towns:
        t = town.strip()
        if t == "E Granby":
            t = "East Granby"
        if t in town_coords:
            lats.append(town_coords[t]["lat"])
            lons.append(town_coords[t]["lon"])
    if lats:
        return sum(lats) / len(lats), sum(lons) / len(lons)
    return None, None


def get_tier(stocked_dates):
    if not stocked_dates:
        return "scheduled", None
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    most_recent = max(datetime.strptime(d, "%Y-%m-%d") for d in stocked_dates)
    days_ago = (today - most_recent).days
    if days_ago <= TIER_HOT:
        return "hot", days_ago
    elif days_ago <= TIER_FRESH:
        return "fresh", days_ago
    else:
        return "aging", days_ago


def build_locations():
    data = json.loads((BASE / "stocking_data.json").read_text())
    town_coords = json.loads((BASE / "ct_town_coords.json").read_text())
    report_date = data["report_date"]
    catch_release = data["catch_and_release_until"][:10]

    locations = []
    for loc in data["all_locations"]:
        lat, lon = get_location_coords(loc["towns"], town_coords)
        if lat is None:
            continue
        dist = haversine_distance(HOME_LOCATION["lat"], HOME_LOCATION["lon"], lat, lon)
        tier, days_ago = get_tier(loc.get("stocked_dates", []))
        stocked_dates = loc.get("stocked_dates", [])
        locations.append({
            "waterbody": loc["waterbody"],
            "towns": ", ".join(loc["towns"]),
            "management_type": loc.get("management_type"),
            "stocked_dates": stocked_dates,
            "tier": tier,
            "days_ago": days_ago,
            "distance": round(dist, 1),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
        })

    locations.sort(key=lambda x: x["distance"])
    return locations, report_date, catch_release


def generate():
    locations, report_date, catch_release = build_locations()
    stocked = [l for l in locations if l["tier"] != "scheduled"]

    locs_json = json.dumps(locations)
    home_json = json.dumps(HOME_LOCATION)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CT Trout Stocking</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f172a; color: #e2e8f0; }}

  header {{ padding: 12px 16px; background: #1e293b; border-bottom: 1px solid #334155; }}
  header h1 {{ font-size: 1.1rem; font-weight: 700; color: #f8fafc; }}
  header p {{ font-size: 0.75rem; color: #94a3b8; margin-top: 2px; }}

  #map {{ height: 45vh; width: 100%; }}

  .legend {{ display: flex; gap: 12px; flex-wrap: wrap; padding: 8px 16px; background: #1e293b; border-bottom: 1px solid #334155; font-size: 0.72rem; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}

  .filter-bar {{ padding: 8px 16px; background: #1e293b; border-bottom: 1px solid #334155; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
  .filter-bar label {{ font-size: 0.75rem; color: #94a3b8; }}
  .filter-bar select, .filter-bar input {{
    background: #0f172a; border: 1px solid #334155; color: #e2e8f0;
    padding: 4px 8px; border-radius: 6px; font-size: 0.8rem;
  }}

  #table-container {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  thead th {{
    position: sticky; top: 0; background: #1e293b;
    padding: 8px 10px; text-align: left; font-weight: 600;
    color: #94a3b8; border-bottom: 1px solid #334155; cursor: pointer;
    white-space: nowrap; user-select: none;
  }}
  thead th:hover {{ color: #f8fafc; }}
  thead th.sorted {{ color: #38bdf8; }}
  tbody tr {{ border-bottom: 1px solid #1e293b; cursor: pointer; transition: background 0.1s; }}
  tbody tr:hover {{ background: #1e293b; }}
  tbody td {{ padding: 9px 10px; vertical-align: top; }}
  .name-cell {{ font-weight: 600; color: #f8fafc; }}
  .mgmt-badge {{
    display: inline-block; font-size: 0.65rem; font-weight: 700;
    padding: 1px 5px; border-radius: 4px; margin-left: 5px;
    background: #334155; color: #94a3b8; vertical-align: middle;
  }}
  .town-cell {{ color: #94a3b8; font-size: 0.75rem; }}
  .dist-cell {{ color: #cbd5e1; white-space: nowrap; }}
  .tier-badge {{
    display: inline-block; font-size: 0.7rem; font-weight: 600;
    padding: 2px 7px; border-radius: 99px; white-space: nowrap;
  }}
  .map-link {{
    display: inline-block; font-size: 0.7rem; color: #38bdf8;
    text-decoration: none; margin-top: 3px;
  }}
  .map-link:hover {{ text-decoration: underline; }}

  .no-results {{ padding: 24px; text-align: center; color: #64748b; }}

  @media (min-width: 640px) {{
    #map {{ height: 50vh; }}
  }}
</style>
</head>
<body>

<header>
  <h1>CT Trout Stocking</h1>
  <p>Report: {report_date} &nbsp;·&nbsp; C&R until {catch_release} &nbsp;·&nbsp; From {HOME_LOCATION['name']}</p>
</header>

<div id="map"></div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div> Hot (0–2d)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div> Fresh (3–5d)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f97316"></div> Aging (6+d)</div>
  <div class="legend-item"><div class="legend-dot" style="background:#a3a3a3"></div> Scheduled</div>
</div>

<div class="filter-bar">
  <label>Filter:</label>
  <select id="tier-filter" onchange="applyFilters()">
    <option value="all">All tiers</option>
    <option value="hot">🔥 Hot</option>
    <option value="fresh">✓ Fresh</option>
    <option value="aging">⏳ Aging</option>
    <option value="scheduled">Scheduled</option>
  </select>
  <select id="dist-filter" onchange="applyFilters()">
    <option value="0">Any distance</option>
    <option value="15">Within 15 mi</option>
    <option value="25">Within 25 mi</option>
    <option value="50">Within 50 mi</option>
  </select>
  <input id="search" type="search" placeholder="Search…" oninput="applyFilters()" style="flex:1; min-width:100px;">
</div>

<div id="table-container">
  <table>
    <thead>
      <tr>
        <th onclick="sortBy('waterbody')" id="th-waterbody">Location</th>
        <th onclick="sortBy('distance')" id="th-distance" class="sorted">Miles ▲</th>
        <th onclick="sortBy('days_ago')" id="th-days_ago">Days</th>
        <th onclick="sortBy('tier')" id="th-tier">Tier</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="no-results" id="no-results" style="display:none">No locations match your filters.</div>
</div>

<script>
const ALL_LOCATIONS = {locs_json};
const HOME = {home_json};
const TIER_COLOR = {json.dumps(TIER_COLOR)};
const TIER_LABEL = {json.dumps(TIER_LABEL)};

// --- Map ---
const map = L.map('map').setView([HOME.lat, HOME.lon], 10);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© OpenStreetMap contributors', maxZoom: 18
}}).addTo(map);

L.circleMarker([HOME.lat, HOME.lon], {{
  radius: 9, color: '#fff', weight: 2, fillColor: '#ef4444', fillOpacity: 1
}}).bindPopup('<b>Home: {HOME_LOCATION["name"]}</b>').addTo(map);

const markerLayer = L.layerGroup().addTo(map);

function makeMarker(loc) {{
  const color = TIER_COLOR[loc.tier];
  const m = L.circleMarker([loc.lat, loc.lon], {{
    radius: loc.tier === 'hot' ? 9 : loc.tier === 'fresh' ? 8 : 7,
    color: '#fff', weight: 1.5, fillColor: color, fillOpacity: 0.85
  }});
  const daysStr = loc.days_ago !== null ? `${{loc.days_ago}}d ago` : 'not yet stocked';
  const mgmt = loc.management_type ? ` [${{loc.management_type}}]` : '';
  const dates = loc.stocked_dates.length ? `<br>Stocked: ${{loc.stocked_dates.join(', ')}}` : '';
  const mapsUrl = `https://www.google.com/maps/search/${{encodeURIComponent(loc.waterbody + ', CT')}}/@${{loc.lat}},${{loc.lon}},14z`;
  m.bindPopup(`<b>${{loc.waterbody}}${{mgmt}}</b><br>${{loc.towns}}<br>${{loc.distance}} mi · ${{daysStr}}${{dates}}<br><a href="${{mapsUrl}}" target="_blank">Open in Google Maps</a>`);
  return m;
}}

// --- Table ---
let sortKey = 'distance';
let sortAsc = true;
let filtered = [...ALL_LOCATIONS];

function tierOrder(t) {{ return {{hot:0,fresh:1,aging:2,scheduled:3}}[t] ?? 4; }}

function sortBy(key) {{
  if (sortKey === key) sortAsc = !sortAsc;
  else {{ sortKey = key; sortAsc = true; }}
  document.querySelectorAll('thead th').forEach(th => th.classList.remove('sorted'));
  const th = document.getElementById('th-' + key);
  if (th) th.classList.add('sorted');
  render();
}}

function applyFilters() {{
  const tier = document.getElementById('tier-filter').value;
  const maxDist = parseFloat(document.getElementById('dist-filter').value) || 0;
  const q = document.getElementById('search').value.toLowerCase();
  filtered = ALL_LOCATIONS.filter(l => {{
    if (tier !== 'all' && l.tier !== tier) return false;
    if (maxDist > 0 && l.distance > maxDist) return false;
    if (q && !l.waterbody.toLowerCase().includes(q) && !l.towns.toLowerCase().includes(q)) return false;
    return true;
  }});
  render();
  updateMarkers();
}}

function render() {{
  const sorted = [...filtered].sort((a, b) => {{
    let av = a[sortKey], bv = b[sortKey];
    if (sortKey === 'tier') {{ av = tierOrder(av); bv = tierOrder(bv); }}
    if (av === null) av = 9999;
    if (bv === null) bv = 9999;
    return sortAsc ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1);
  }});

  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  document.getElementById('no-results').style.display = sorted.length ? 'none' : 'block';

  sorted.forEach(loc => {{
    const mgmt = loc.management_type ? `<span class="mgmt-badge">${{loc.management_type}}</span>` : '';
    const daysStr = loc.days_ago !== null ? loc.days_ago + 'd' : '—';
    const color = TIER_COLOR[loc.tier];
    const label = TIER_LABEL[loc.tier];
    const mapsUrl = `https://www.google.com/maps/search/${{encodeURIComponent(loc.waterbody + ', CT')}}/@${{loc.lat}},${{loc.lon}},14z`;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="name-cell">${{loc.waterbody}}${{mgmt}}</div>
        <div class="town-cell">${{loc.towns}}</div>
        <a class="map-link" href="${{mapsUrl}}" target="_blank">📍 Maps</a>
      </td>
      <td class="dist-cell">${{loc.distance}} mi</td>
      <td class="dist-cell">${{daysStr}}</td>
      <td><span class="tier-badge" style="background:${{color}}22;color:${{color}}">${{label}}</span></td>
    `;
    tr.addEventListener('click', (e) => {{
      if (e.target.tagName === 'A') return;
      map.setView([loc.lat, loc.lon], 13);
      window.scrollTo({{top: 0, behavior: 'smooth'}});
    }});
    tbody.appendChild(tr);
  }});
}}

function updateMarkers() {{
  markerLayer.clearLayers();
  filtered.forEach(loc => makeMarker(loc).addTo(markerLayer));
}}

applyFilters();
</script>
</body>
</html>"""

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(html)
    print(f"Generated: {OUTPUT}")
    print(f"  {len(stocked)} stocked locations, {len(locations)} total")


if __name__ == "__main__":
    generate()

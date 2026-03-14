"""Integration tests — verifies real data files load and produce valid results."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from find_stocked import load_data, load_town_coords, get_recently_stocked_with_distance
from generate_kml import generate_kml


class TestDataFiles:
    def test_stocking_data_loads(self):
        data = load_data()
        assert "report_date" in data
        assert "recently_stocked" in data
        assert "all_locations" in data
        assert "catch_and_release_until" in data

    def test_report_date_format(self):
        data = load_data()
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", data["report_date"])

    def test_all_locations_not_empty(self):
        data = load_data()
        assert len(data["all_locations"]) > 0

    def test_location_has_required_fields(self):
        data = load_data()
        for loc in data["all_locations"]:
            assert "waterbody" in loc
            assert "towns" in loc
            assert isinstance(loc["towns"], list)
            assert len(loc["towns"]) > 0

    def test_town_coords_loads(self):
        coords = load_town_coords()
        assert len(coords) > 100  # CT has 169 towns

    def test_town_coords_have_lat_lon(self):
        coords = load_town_coords()
        for town, data in coords.items():
            assert "lat" in data, f"{town} missing lat"
            assert "lon" in data, f"{town} missing lon"
            # CT bounding box sanity check
            assert 40.9 < data["lat"] < 42.1, f"{town} lat out of CT range"
            assert -73.8 < data["lon"] < -71.7, f"{town} lon out of CT range"


class TestGetRecentlyStocked:
    def test_returns_results_and_date(self):
        results, report_date = get_recently_stocked_with_distance()
        assert isinstance(results, list)
        assert isinstance(report_date, str)

    def test_results_sorted_by_distance(self):
        results, _ = get_recently_stocked_with_distance()
        if len(results) > 1:
            distances = [r["distance_miles"] for r in results]
            assert distances == sorted(distances)

    def test_result_fields(self):
        results, _ = get_recently_stocked_with_distance()
        for r in results:
            assert "waterbody" in r
            assert "distance_miles" in r
            assert "tier" in r
            assert r["tier"] in ("hot", "fresh", "aging")
            assert "days_ago" in r
            assert r["distance_miles"] >= 0

    def test_custom_home_location(self):
        # Hartford, CT
        results, _ = get_recently_stocked_with_distance(home_lat=41.7637, home_lon=-72.6851)
        assert len(results) > 0
        # Closest should be within CT (~100 miles max)
        assert results[0]["distance_miles"] < 100


class TestGenerateKml:
    def test_kml_is_valid_xml(self):
        import xml.etree.ElementTree as ET
        kml_content, locations, tiers = generate_kml()
        # Should not raise
        ET.fromstring(kml_content)

    def test_kml_has_placemarks(self):
        kml_content, locations, tiers = generate_kml()
        assert "<Placemark>" in kml_content

    def test_tiers_keys_present(self):
        _, _, tiers = generate_kml()
        assert set(tiers.keys()) == {"hot", "fresh", "aging", "scheduled"}

    def test_locations_within_distance(self):
        from generate_kml import MAX_DISTANCE_MILES
        _, locations, _ = generate_kml()
        for loc in locations:
            assert loc["distance"] <= MAX_DISTANCE_MILES

"""Tests for find_stocked.py"""
import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from find_stocked import (
    haversine_distance,
    get_location_coords,
    get_recency_tier,
    get_tier_symbol,
    get_tier_label,
)

SAMPLE_TOWN_COORDS = {
    "Redding":      {"lat": 41.3034, "lon": -73.3832},
    "New Hartford": {"lat": 41.8748, "lon": -72.9737},
    "East Granby":  {"lat": 41.9565, "lon": -72.7290},
}

FIXED_TODAY = datetime(2026, 3, 12)


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(41.3, -73.3, 41.3, -73.3) == pytest.approx(0.0, abs=0.01)

    def test_known_distance(self):
        # Redding CT to New York City (~50 miles)
        dist = haversine_distance(41.3034, -73.3832, 40.7128, -74.0060)
        assert 45 < dist < 60

    def test_symmetry(self):
        d1 = haversine_distance(41.3, -73.3, 41.8, -72.9)
        d2 = haversine_distance(41.8, -72.9, 41.3, -73.3)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_positive_result(self):
        dist = haversine_distance(41.0, -73.0, 42.0, -72.0)
        assert dist > 0


class TestGetLocationCoords:
    def test_single_known_town(self):
        lat, lon = get_location_coords(["Redding"], SAMPLE_TOWN_COORDS)
        assert lat == pytest.approx(41.3034)
        assert lon == pytest.approx(-73.3832)

    def test_multiple_towns_averages(self):
        lat, lon = get_location_coords(["Redding", "New Hartford"], SAMPLE_TOWN_COORDS)
        assert lat == pytest.approx((41.3034 + 41.8748) / 2)
        assert lon == pytest.approx((-73.3832 + -72.9737) / 2)

    def test_unknown_town_returns_none(self):
        lat, lon = get_location_coords(["UnknownTown"], SAMPLE_TOWN_COORDS)
        assert lat is None
        assert lon is None

    def test_e_granby_alias(self):
        lat, lon = get_location_coords(["E Granby"], SAMPLE_TOWN_COORDS)
        assert lat == pytest.approx(41.9565)
        assert lon == pytest.approx(-72.7290)

    def test_mixed_known_unknown_uses_known(self):
        lat, lon = get_location_coords(["Redding", "Narnia"], SAMPLE_TOWN_COORDS)
        assert lat == pytest.approx(41.3034)
        assert lon == pytest.approx(-73.3832)

    def test_empty_town_list_returns_none(self):
        lat, lon = get_location_coords([], SAMPLE_TOWN_COORDS)
        assert lat is None
        assert lon is None


class TestGetRecencyTier:
    def test_hot_zero_days(self):
        with patch("find_stocked.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            tier, days = get_recency_tier("2026-03-12", "2026-03-12")
        assert tier == "hot"
        assert days == 0

    def test_hot_two_days(self):
        with patch("find_stocked.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            tier, days = get_recency_tier("2026-03-10", "2026-03-12")
        assert tier == "hot"
        assert days == 2

    def test_fresh_three_days(self):
        with patch("find_stocked.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            tier, days = get_recency_tier("2026-03-09", "2026-03-12")
        assert tier == "fresh"
        assert days == 3

    def test_fresh_five_days(self):
        with patch("find_stocked.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            tier, days = get_recency_tier("2026-03-07", "2026-03-12")
        assert tier == "fresh"
        assert days == 5

    def test_aging_six_days(self):
        with patch("find_stocked.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            tier, days = get_recency_tier("2026-03-06", "2026-03-12")
        assert tier == "aging"
        assert days == 6


class TestTierLabels:
    def test_symbols(self):
        assert get_tier_symbol("hot") == "🔥"
        assert get_tier_symbol("fresh") == "✓"
        assert get_tier_symbol("aging") == "⏳"
        assert get_tier_symbol("unknown") == " "

    def test_labels(self):
        assert get_tier_label("hot") == "HOT"
        assert get_tier_label("fresh") == "FRESH"
        assert get_tier_label("aging") == "AGING"
        assert get_tier_label("unknown") == ""

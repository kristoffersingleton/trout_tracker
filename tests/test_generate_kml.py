"""Tests for generate_kml.py"""
import pytest
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_kml import (
    escape_xml,
    get_recency_tier,
    get_days_since,
)

FIXED_TODAY = datetime(2026, 3, 11)


class TestEscapeXml:
    def test_ampersand(self):
        assert escape_xml("Tom & Jerry") == "Tom &amp; Jerry"

    def test_less_than(self):
        assert escape_xml("a < b") == "a &lt; b"

    def test_greater_than(self):
        assert escape_xml("a > b") == "a &gt; b"

    def test_single_quote(self):
        assert escape_xml("it's") == "it&apos;s"

    def test_double_quote(self):
        assert escape_xml('say "hi"') == "say &quot;hi&quot;"

    def test_no_special_chars(self):
        assert escape_xml("Farmington River") == "Farmington River"

    def test_multiple_special_chars(self):
        result = escape_xml('<a href="url">Tom & Jerry</a>')
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result
        assert "&quot;" in result


class TestKmlRecencyTier:
    def _tier(self, dates, report="2026-03-11"):
        with patch("generate_kml.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            return get_recency_tier(dates, report)

    def test_scheduled_no_dates(self):
        assert self._tier([]) == "scheduled"

    def test_hot_same_day(self):
        assert self._tier(["2026-03-11"]) == "hot"

    def test_hot_one_day(self):
        assert self._tier(["2026-03-10"]) == "hot"

    def test_hot_two_days(self):
        assert self._tier(["2026-03-09"]) == "hot"

    def test_fresh_three_days(self):
        assert self._tier(["2026-03-08"]) == "fresh"

    def test_fresh_five_days(self):
        assert self._tier(["2026-03-06"]) == "fresh"

    def test_aging_six_days(self):
        assert self._tier(["2026-03-05"]) == "aging"

    def test_uses_most_recent_date(self):
        # Multiple dates — most recent (3/10) is 1 day ago → hot
        assert self._tier(["2026-03-01", "2026-03-10"]) == "hot"


class TestGetDaysSince:
    def _days(self, dates, report="2026-03-11"):
        with patch("generate_kml.datetime") as mock_dt:
            mock_dt.today.return_value = FIXED_TODAY
            mock_dt.strptime.side_effect = datetime.strptime
            return get_days_since(dates, report)

    def test_same_day(self):
        assert self._days(["2026-03-11"]) == 0

    def test_one_day(self):
        assert self._days(["2026-03-10"]) == 1

    def test_uses_most_recent(self):
        assert self._days(["2026-03-01", "2026-03-09"]) == 2

    def test_empty_returns_none(self):
        assert self._days([]) is None

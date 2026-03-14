"""Tests for parse_pdf.py"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from parse_pdf import (
    parse_report_date,
    parse_catch_release_date,
    parse_stocked_dates,
    parse_waterbody,
    is_table1_header,
    is_table2_header,
)


class TestParseReportDate:
    def test_standard_format(self):
        text = "STOCKING UPDATE AS OF 03/11/2026 - some other text"
        assert parse_report_date(text) == "2026-03-11"

    def test_single_digit_month_day(self):
        text = "STOCKING UPDATE AS OF 03/09/2026"
        assert parse_report_date(text) == "2026-03-09"

    def test_missing_date_raises(self):
        with pytest.raises(ValueError):
            parse_report_date("No date here")


class TestParseCatchReleaseDate:
    def test_april_date_extracted(self):
        text = "catch and release until 6:00 am on Saturday, April (April 11th)"
        result = parse_catch_release_date(text, "2026")
        assert result == "2026-04-11T06:00:00"

    def test_fallback_april_11(self):
        result = parse_catch_release_date("no date here at all", "2026")
        assert result == "2026-04-11T06:00:00"


class TestParseStockedDates:
    def test_single_date(self):
        assert parse_stocked_dates("3/2", "2026") == ["2026-03-02"]

    def test_multiple_dates(self):
        result = parse_stocked_dates("3/3, 3/4", "2026")
        assert result == ["2026-03-03", "2026-03-04"]

    def test_empty_string(self):
        assert parse_stocked_dates("", "2026") == []

    def test_none(self):
        assert parse_stocked_dates(None, "2026") == []

    def test_whitespace_only(self):
        assert parse_stocked_dates("   ", "2026") == []

    def test_single_digit_day(self):
        assert parse_stocked_dates("3/9", "2026") == ["2026-03-09"]


class TestParseWaterbody:
    def test_em_dash_separator(self):
        name, mgmt = parse_waterbody("Salmon Creek – TML")
        assert name == "Salmon Creek"
        assert mgmt == "TML"

    def test_spaced_dash_separator(self):
        name, mgmt = parse_waterbody("Pine Lake - TML")
        assert name == "Pine Lake"
        assert mgmt == "TML"

    def test_no_management_type(self):
        name, mgmt = parse_waterbody("Farmington River")
        assert name == "Farmington River"
        assert mgmt is None

    def test_strips_whitespace(self):
        name, mgmt = parse_waterbody("  Saugatuck Reservoir – TML  ")
        assert name == "Saugatuck Reservoir"
        assert mgmt == "TML"


class TestTableHeaderDetection:
    def test_table1_header_detected(self):
        assert is_table1_header(["Waterbody (Alphabetically) – Management type", "Town(s)", "Date(s) stocked"])

    def test_table2_header_detected(self):
        assert is_table2_header(["Waterbody – Management type", "Town(s)", "Date(s) stocked"])

    def test_table1_header_not_table2(self):
        assert not is_table2_header(["Waterbody (Alphabetically) – Management type", "Town(s)"])

    def test_empty_row_not_header(self):
        assert not is_table1_header([])
        assert not is_table2_header([])

    def test_none_cell_not_header(self):
        assert not is_table1_header([None, "Town"])
        assert not is_table2_header([None, "Town"])

    def test_regular_data_row_not_header(self):
        assert not is_table1_header(["Farmington River", "New Hartford", "3/9"])
        assert not is_table2_header(["Farmington River", "New Hartford", "3/9"])

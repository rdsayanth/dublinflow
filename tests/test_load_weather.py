"""Tests for reading the Met Eireann hourly weather file (no download, no database)."""

import pytest

import load_weather_to_postgres as weather

HEADER = ",".join(weather.FILE_HEADER)
ROW = "01-oct-2025 00:00,0,0.2,0,11.3,0,10.6,9.9,12.2,91,1012.3,2,9,2,240,2,11,0.0,30000,25,7"


def write(tmp_path, text):
    path = tmp_path / "hly532.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_read_rows_skips_description_lines(tmp_path):
    path = write(tmp_path, f"Station Name: DUBLIN AIRPORT\nLatitude:53.428\n\n{HEADER}\n{ROW}\n{ROW}\n")

    rows = list(weather.read_rows(path))

    assert len(rows) == 2
    assert rows[0][0] == "01-oct-2025 00:00"
    assert len(rows[0]) == len(weather.FILE_HEADER)


def test_read_rows_rejects_changed_columns(tmp_path):
    path = write(tmp_path, "date,rain,temp\n01-oct-2025 00:00,0.2,11.3\n")

    with pytest.raises(ValueError, match="unexpected columns"):
        list(weather.read_rows(path))


def test_read_rows_needs_a_header(tmp_path):
    path = write(tmp_path, "Station Name: DUBLIN AIRPORT\nno data here\n")

    with pytest.raises(ValueError, match="header line"):
        list(weather.read_rows(path))


def test_read_rows_rejects_short_rows(tmp_path):
    path = write(tmp_path, f"{HEADER}\n{ROW}\n01-oct-2025 01:00,0,0.0\n")

    with pytest.raises(ValueError, match="fields"):
        list(weather.read_rows(path))


def test_columns_match_file_header():
    # Every file column gets exactly one name in the database table.
    assert len(weather.COLUMNS) == len(weather.FILE_HEADER)
    assert len(set(weather.COLUMNS)) == len(weather.COLUMNS)

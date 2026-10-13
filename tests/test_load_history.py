"""Tests for loading Smart Dublin history files (no database: a fake connection records the rows)."""

from contextlib import contextmanager

import pytest

import load_history_to_postgres as history


class FakeCopy:
    def __init__(self, rows):
        self.rows = rows

    def write_row(self, row):
        self.rows.append(row)


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @contextmanager
    def copy(self, sql):
        self.conn.copy_sql = sql
        yield FakeCopy(self.conn.copied)

    def execute(self, sql, params):
        self.conn.executed.append((sql, params))


class FakeConnection:
    def __init__(self):
        self.copied, self.executed, self.copy_sql = [], [], None

    @contextmanager
    def transaction(self):
        yield

    def cursor(self):
        return FakeCursor(self)


def write_csv(tmp_path, header, rows, name="dublinbikes_202501.csv", bom=True):
    lines = [",".join(header)] + [",".join(r) for r in rows]
    path = tmp_path / name
    path.write_text(("﻿" if bom else "") + "\n".join(lines) + "\n", encoding="utf-8")
    return path


def sample_row(i):
    return [str(i)] * len(history.EXPECTED_HEADER)


def test_load_file_copies_rows_with_source_file(tmp_path):
    path = write_csv(tmp_path, history.EXPECTED_HEADER, [sample_row(1), sample_row(2)])
    conn = FakeConnection()

    rows = history.load_file(conn, path)

    assert rows == 2
    assert conn.copied[0] == sample_row(1) + ["dublinbikes_202501.csv"]
    assert conn.executed[-1][1] == ("dublinbikes_202501.csv", 2)  # file recorded with its row count


def test_load_file_handles_byte_order_mark(tmp_path):
    # Smart Dublin CSVs start with a UTF-8 BOM; the header must still match.
    path = write_csv(tmp_path, history.EXPECTED_HEADER, [sample_row(1)], bom=True)

    assert history.load_file(FakeConnection(), path) == 1


def test_load_file_rejects_changed_columns(tmp_path):
    wrong = list(history.EXPECTED_HEADER)
    wrong[0] = "renamed_column"
    path = write_csv(tmp_path, wrong, [sample_row(1)])
    conn = FakeConnection()

    with pytest.raises(ValueError, match="unexpected columns"):
        history.load_file(conn, path)
    assert conn.copied == []  # nothing loaded

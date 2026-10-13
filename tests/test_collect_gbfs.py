"""Tests for the live feed collector (no network, no Azure)."""

import json

import pytest
import requests

import collect_gbfs


class FakeResponse:
    """Just enough of requests.Response for save_raw."""

    def __init__(self, payload):
        self.text = json.dumps(payload)

    def json(self):
        return json.loads(self.text)


def snapshot(stations, last_updated=1760083200):  # 2025-10-10 08:00:00 UTC
    return {"last_updated": last_updated, "ttl": 60, "data": {"stations": stations}}


def test_save_raw_names_file_by_feed_time(tmp_path, monkeypatch):
    monkeypatch.setattr(collect_gbfs, "RAW_DIR", tmp_path)
    response = FakeResponse(snapshot([{"station_id": "1", "num_bikes_available": 5}]))

    path = collect_gbfs.save_raw("station_status", response)

    assert path == "station_status/2025-10-10/station_status_20251010T080000Z.json"
    saved = tmp_path / path
    assert saved.read_text(encoding="utf-8") == response.text  # saved unchanged


def test_save_raw_rejects_empty_feed(tmp_path, monkeypatch):
    monkeypatch.setattr(collect_gbfs, "RAW_DIR", tmp_path)

    with pytest.raises(ValueError, match="0 stations"):
        collect_gbfs.save_raw("station_status", FakeResponse(snapshot([])))
    assert not any(tmp_path.rglob("*.json"))  # nothing written


def test_fetch_feed_retries_then_succeeds(monkeypatch):
    calls = []

    class OkResponse:
        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        calls.append(url)
        if len(calls) < 3:
            raise requests.ConnectionError("network down")
        return OkResponse()

    monkeypatch.setattr(collect_gbfs.requests, "get", fake_get)
    monkeypatch.setattr(collect_gbfs.time, "sleep", lambda seconds: None)

    response = collect_gbfs.fetch_feed("station_status")

    assert isinstance(response, OkResponse)
    assert len(calls) == 3
    assert calls[0].endswith("/station_status.json")


def test_fetch_feed_gives_up_after_max_attempts(monkeypatch):
    def always_fail(url, timeout):
        raise requests.Timeout("too slow")

    monkeypatch.setattr(collect_gbfs.requests, "get", always_fail)
    monkeypatch.setattr(collect_gbfs.time, "sleep", lambda seconds: None)

    with pytest.raises(requests.Timeout):
        collect_gbfs.fetch_feed("station_information")

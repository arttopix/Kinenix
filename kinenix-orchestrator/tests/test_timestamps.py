import datetime

import pytest
from fastapi.testclient import TestClient

from kinenix_orchestrator import config as orchestrator_config
from kinenix_orchestrator.app import app
from kinenix_orchestrator.timeutils import isoformat_utc, parse_timestamp, to_utc_naive

client = TestClient(app, client=("127.0.0.1", 50000))


@pytest.fixture(autouse=True)
def no_credentials(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "")


def _ingest(log_payload):
    res = client.post("/api/v1/telemetry", json={"worker_id": "tz-worker", "payload": log_payload})
    assert res.status_code == 200
    return client.get(f"/api/v1/executions/{res.json()['execution_id']}").json()


def test_heartbeat_is_serialized_as_current_utc():
    client.post("/api/v1/heartbeat", json={"worker_id": "tz-heartbeat", "name": "TZ Node"})
    workers = client.get("/api/v1/workers").json()["workers"]
    last = next(w["last_heartbeat"] for w in workers if w["id"] == "tz-heartbeat")

    parsed = datetime.datetime.fromisoformat(last)
    assert parsed.utcoffset() == datetime.timedelta(0)
    # A browser must read this as "just now", not hours away
    now = datetime.datetime.now(datetime.timezone.utc)
    assert abs((now - parsed).total_seconds()) < 60


def test_offset_timestamps_are_converted_to_utc():
    execution = _ingest({
        "flow_name": "TZ Offset",
        "start_time": "2026-09-21T18:00:00+07:00",
        "end_time": "2026-09-21T18:00:10+07:00",
        "metrics": {"total_duration_seconds": 10.0},
    })
    assert execution["start_time"] == "2026-09-21T11:00:00+00:00"
    assert execution["end_time"] == "2026-09-21T11:00:10+00:00"


def test_missing_end_time_is_derived_from_duration():
    # kinenix-core execution logs have start_time and a duration but no end_time
    execution = _ingest({
        "flow_name": "TZ No End",
        "start_time": "2026-09-21 18:00:00.500000+07:00",
        "metrics": {"total_duration_seconds": 12.5},
    })
    assert execution["start_time"] == "2026-09-21T11:00:00.500000+00:00"
    assert execution["end_time"] == "2026-09-21T11:00:13+00:00"


def test_invalid_start_time_falls_back_to_now():
    execution = _ingest({"flow_name": "TZ Invalid", "start_time": "not-a-date"})
    parsed = datetime.datetime.fromisoformat(execution["start_time"])
    now = datetime.datetime.now(datetime.timezone.utc)
    assert abs((now - parsed).total_seconds()) < 60


def test_parse_timestamp_accepts_z_suffix():
    assert parse_timestamp("2026-09-21T11:00:00Z") == datetime.datetime(2026, 9, 21, 11, 0, 0)


def test_parse_timestamp_treats_naive_input_as_host_local_time():
    naive = datetime.datetime(2026, 9, 21, 18, 0, 0)
    expected = naive.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    assert parse_timestamp("2026-09-21T18:00:00") == expected
    assert to_utc_naive(naive) == expected


def test_isoformat_utc():
    assert isoformat_utc(None) is None
    assert isoformat_utc(datetime.datetime(2026, 9, 21, 11, 0, 0)) == "2026-09-21T11:00:00+00:00"

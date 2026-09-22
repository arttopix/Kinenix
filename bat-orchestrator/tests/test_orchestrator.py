import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from importlib import import_module
orchestrator_app = import_module("bat-orchestrator.app")
app = orchestrator_app.app

client = TestClient(app)


def test_orchestrator_healthz():
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_heartbeat_api():
    payload = {
        "worker_id": "rpi-test-01",
        "name": "Raspberry Pi Node",
        "ip_address": "192.168.1.100",
        "os_info": "Raspberry Pi OS",
        "cpu_percent": 12.5,
        "ram_usage": "1.2 / 8 GB",
        "current_task": "BOT"
    }
    response = client.post("/api/v1/heartbeat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["worker"]["id"] == "rpi-test-01"
    assert data["worker"]["status"] == "busy"

    # Verify listing
    res_list = client.get("/api/v1/workers")
    assert res_list.status_code == 200
    workers = res_list.json()["workers"]
    assert any(w["id"] == "rpi-test-01" for w in workers)


def test_telemetry_ingestion_success():
    log_payload = {
        "flow_name": "RPA Challenge",
        "start_time": "2026-09-21T18:00:00",
        "end_time": "2026-09-21T18:00:10",
        "has_error": False,
        "metrics": {
            "total_duration_seconds": 10.0,
            "total_steps": 5,
            "successful_steps": 5,
            "failed_steps": 0
        }
    }
    req = {
        "worker_id": "rpi-test-01",
        "payload": log_payload
    }
    response = client.post("/api/v1/telemetry", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["has_error"] is False


def test_telemetry_ingestion_failure_with_ai():
    log_payload = {
        "flow_name": "BOT Exchange Rates",
        "start_time": "2026-09-21T18:30:00",
        "end_time": "2026-09-21T18:30:15",
        "has_error": True,
        "failure_details": {
            "failed_step_id": "step_4",
            "failed_step_name": "Click Cookie Consent Button",
            "error_type": "Technical",
            "exception_class": "TimeoutError",
            "error_message": "Timeout 3000ms exceeded while waiting for button:has-text('Accept recommended cookies')"
        },
        "metrics": {
            "total_duration_seconds": 15.0,
            "total_steps": 4,
            "successful_steps": 3,
            "failed_steps": 1
        }
    }
    req = {
        "worker_id": "rpi-test-01",
        "payload": log_payload
    }

    # Mock OpenThai-SystemOne HTTP response
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choice": "Cookie Consent / Security Modal",
                "score": 0.94
            }
        )
        response = client.post("/api/v1/telemetry", json=req)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recorded"
        assert data["has_error"] is True
        assert "Cookie" in data["ai_summary"]


def test_list_executions():
    response = client.get("/api/v1/executions")
    assert response.status_code == 200
    items = response.json()["executions"]
    assert len(items) >= 2


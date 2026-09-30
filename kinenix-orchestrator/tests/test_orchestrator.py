import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from kinenix_orchestrator import config as orchestrator_config
from kinenix_orchestrator.app import app

# Local-dev client: no API key configured, requests arrive from loopback
client = TestClient(app, client=("127.0.0.1", 50000))
remote_client = TestClient(app, client=("192.168.1.77", 50000))

HEARTBEAT_PAYLOAD = {"worker_id": "rpi-auth-01", "name": "Auth Test Node"}


@pytest.fixture(autouse=True)
def no_credentials_by_default(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_USER", "admin")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "")


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



def test_remote_worker_rejected_when_api_key_not_configured():
    response = remote_client.post("/api/v1/heartbeat", json=HEARTBEAT_PAYLOAD)
    assert response.status_code == 403


def test_remote_worker_missing_api_key_rejected(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    response = remote_client.post("/api/v1/heartbeat", json=HEARTBEAT_PAYLOAD)
    assert response.status_code == 401


def test_remote_worker_wrong_api_key_rejected(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    response = remote_client.post(
        "/api/v1/telemetry",
        json={"worker_id": "rpi-auth-01", "payload": {"flow_name": "X"}},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_remote_worker_valid_api_key_accepted(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    response = remote_client.post(
        "/api/v1/heartbeat", json=HEARTBEAT_PAYLOAD, headers={"X-API-Key": "s3cret-key"}
    )
    assert response.status_code == 200
    assert response.json()["worker"]["id"] == "rpi-auth-01"


def test_localhost_must_send_api_key_once_configured(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    response = client.post("/api/v1/heartbeat", json=HEARTBEAT_PAYLOAD)
    assert response.status_code == 401


def test_reanalyze_requires_api_key(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    response = remote_client.post("/api/v1/executions/any-id/reanalyze")
    assert response.status_code == 401


def test_healthz_remains_public(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    assert remote_client.get("/api/v1/healthz").status_code == 200


DASHBOARD_PATHS = ["/", "/api/v1/workers", "/api/v1/executions"]


@pytest.mark.parametrize("path", DASHBOARD_PATHS)
def test_remote_dashboard_rejected_when_password_not_configured(path):
    response = remote_client.get(path)
    assert response.status_code == 403


@pytest.mark.parametrize("path", DASHBOARD_PATHS)
def test_remote_dashboard_missing_credentials_prompts_login(monkeypatch, path):
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    response = remote_client.get(path)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"].startswith("Basic")


@pytest.mark.parametrize("auth", [("admin", "wrong-pass"), ("intruder", "dash-pass")])
def test_remote_dashboard_wrong_credentials_rejected(monkeypatch, auth):
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    response = remote_client.get("/api/v1/executions", auth=auth)
    assert response.status_code == 401


@pytest.mark.parametrize("path", DASHBOARD_PATHS)
def test_remote_dashboard_valid_credentials_accepted(monkeypatch, path):
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    response = remote_client.get(path, auth=("admin", "dash-pass"))
    assert response.status_code == 200


def test_localhost_dashboard_requires_credentials_once_configured(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    response = client.get("/api/v1/workers")
    assert response.status_code == 401


def test_worker_api_key_does_not_grant_dashboard_access(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "API_KEY", "s3cret-key")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "dash-pass")
    response = remote_client.get("/api/v1/executions", headers={"X-API-Key": "s3cret-key"})
    assert response.status_code == 401


def test_cross_origin_requests_get_no_cors_headers():
    response = client.get("/api/v1/healthz", headers={"Origin": "https://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_is_not_allowed():
    response = client.options(
        "/api/v1/executions",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_default_host_is_localhost(monkeypatch):
    import importlib
    monkeypatch.delenv("ORCHESTRATOR_HOST", raising=False)
    try:
        assert importlib.reload(orchestrator_config).HOST == "127.0.0.1"
    finally:
        monkeypatch.undo()
        importlib.reload(orchestrator_config)

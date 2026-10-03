from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests
from rich.console import Console

from kinenix_orchestrator import console as orch_console
from kinenix_orchestrator.settings_file import read_settings, verify_password, write_settings

NOW = datetime(2026, 10, 3, 12, 0, 0, tzinfo=timezone.utc)


def _console() -> Console:
    return Console(record=True, width=160, color_system=None)


def test_browser_urls_never_offer_wildcard_address(monkeypatch):
    monkeypatch.setattr(orch_console, "lan_ip", lambda: "192.168.1.132")
    assert orch_console.browser_urls("0.0.0.0", 8080) == ["http://127.0.0.1:8080", "http://192.168.1.132:8080"]
    assert orch_console.browser_urls("127.0.0.1", 9000) == ["http://127.0.0.1:9000"]

    monkeypatch.setattr(orch_console, "lan_ip", lambda: None)
    assert orch_console.browser_urls("0.0.0.0", 8080) == ["http://127.0.0.1:8080"]


def test_banner_shows_worker_url_and_auth_state(monkeypatch):
    monkeypatch.setattr(orch_console, "lan_ip", lambda: "192.168.1.132")
    console = _console()
    orch_console.print_banner(console, "0.0.0.0", 8080, "http://127.0.0.1:8000/v1/systemone",
                              api_key_set=True, dashboard_password_set=False)
    out = console.export_text()
    assert "http://192.168.1.132:8080" in out
    assert "localhost viewers only" in out
    assert "http://0.0.0.0" not in out


def test_bind_url_log_line_is_hidden():
    import logging
    hide = orch_console._HideBindUrl()
    make = lambda msg: logging.LogRecord("uvicorn.error", logging.INFO, "", 0, msg, None, None)
    assert not hide.filter(make("Uvicorn running on %s://%s:%d (Press CTRL+C to quit)"))
    assert hide.filter(make("Application startup complete."))


@pytest.mark.parametrize("timestamp, expected", [
    ("2026-10-03T11:59:55+00:00", "5s ago"),
    ("2026-10-03T11:45:00+00:00", "15m ago"),
    ("2026-10-03T09:00:00", "3h ago"),
    ("2026-09-30T12:00:00+00:00", "3d ago"),
    (None, "-"),
])
def test_ago(timestamp, expected):
    assert orch_console._ago(timestamp, NOW) == expected


def test_print_status_renders_workers_and_failures():
    data = {
        "workers": [{
            "id": "rpi4-01", "ip_address": "192.168.1.50", "status": "busy", "current_task": "RPA Challenge",
            "cpu_percent": 41.2, "ram_usage": "0.9 / 1.8 GB", "last_heartbeat": "2026-10-03T11:59:58+00:00",
        }],
        "executions": [{
            "flow_name": "RPA Challenge", "worker_id": "rpi4-01", "status": "failed", "duration_seconds": 8.42,
            "has_error": True, "ai_summary": "Selector not found on submit button", "created_at": "2026-10-03T11:58:00+00:00",
        }],
    }
    console = _console()
    orch_console.print_status(console, "http://127.0.0.1:8080", data, now=NOW)
    out = console.export_text()
    for expected in ("rpi4-01", "busy", "41%", "2s ago", "failed", "8.4s", "Selector not found", "2m ago"):
        assert expected in out


def test_print_status_empty():
    console = _console()
    orch_console.print_status(console, "http://127.0.0.1:8080", {"workers": [], "executions": []})
    out = console.export_text()
    assert "No workers" in out and "No executions" in out


def _scripted_console(monkeypatch, *answers) -> Console:
    """Console whose input() returns the given answers in order, for plain and hidden prompts alike."""
    console = _console()
    queue = list(answers)
    monkeypatch.setattr(console, "input", lambda prompt="", password=False: queue.pop(0))
    return console


def test_setup_first_run_generates_key_and_hashes_password(monkeypatch, tmp_path):
    path = tmp_path / "orchestrator.env"
    # remote? port, api key (generate), password, typo repeat, password, repeat
    console = _scripted_console(monkeypatch, "", "", "", "first", "typo", "second", "second")
    values = orch_console.run_setup(console, path)
    out = console.export_text()

    saved = read_settings(path)
    assert saved == values
    assert saved["ORCHESTRATOR_HOST"] == "0.0.0.0"
    assert saved["ORCHESTRATOR_PORT"] == "8080"
    assert len(saved["ORCHESTRATOR_API_KEY"]) >= 40 and saved["ORCHESTRATOR_API_KEY"] in out
    assert "second" not in path.read_text(encoding="utf-8")
    assert verify_password("second", saved["ORCHESTRATOR_DASHBOARD_PASSWORD_HASH"])
    assert "Passwords do not match" in out


def test_setup_rerun_keeps_existing_credentials(monkeypatch, tmp_path):
    path = tmp_path / "orchestrator.env"
    write_settings(path, {"ORCHESTRATOR_HOST": "0.0.0.0", "ORCHESTRATOR_PORT": "8080",
                          "ORCHESTRATOR_API_KEY": "old-key", "ORCHESTRATOR_DASHBOARD_PASSWORD_HASH": "h"})
    # keep remote, change port, keep key, keep password
    values = orch_console.run_setup(_scripted_console(monkeypatch, "", "9000", "", ""), path)
    assert values == {"ORCHESTRATOR_HOST": "0.0.0.0", "ORCHESTRATOR_PORT": "9000",
                      "ORCHESTRATOR_API_KEY": "old-key", "ORCHESTRATOR_DASHBOARD_PASSWORD_HASH": "h"}


def test_setup_local_only_asks_no_credentials(monkeypatch, tmp_path):
    path = tmp_path / "orchestrator.env"
    console = _scripted_console(monkeypatch, "maybe", "n", "abc", "8081")
    values = orch_console.run_setup(console, path)
    assert values == {"ORCHESTRATOR_HOST": "127.0.0.1", "ORCHESTRATOR_PORT": "8081"}
    out = console.export_text()
    assert "Please answer y or n" in out and "between 1 and 65535" in out


def test_fetch_status_passes_auth_and_raises_on_http_error():
    ok = MagicMock(status_code=200)
    ok.json.side_effect = [{"workers": [{"id": "w"}]}, {"executions": []}]
    with patch("kinenix_orchestrator.console.requests.get", return_value=ok) as get:
        data = orch_console.fetch_status("http://orch:8080/", ("admin", "pw"), 5)
    assert data == {"workers": [{"id": "w"}], "executions": []}
    assert get.call_args_list[0].args[0] == "http://orch:8080/api/v1/workers"
    assert get.call_args_list[1].kwargs["params"] == {"limit": 5}
    assert all(c.kwargs["auth"] == ("admin", "pw") for c in get.call_args_list)

    denied = MagicMock(status_code=401)
    denied.raise_for_status.side_effect = requests.HTTPError(response=denied)
    with patch("kinenix_orchestrator.console.requests.get", return_value=denied):
        with pytest.raises(requests.HTTPError):
            orch_console.fetch_status("http://orch:8080", None, 5)

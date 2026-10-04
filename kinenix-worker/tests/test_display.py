from rich.console import Console

from kinenix_worker import display
from kinenix_worker.hub_client import HubClient


def _console() -> Console:
    return Console(record=True, width=120, color_system=None)


def test_print_ping_shows_connection_fields():
    console = _console()
    client = HubClient(url="http://orch:8080", api_key="k", worker_id="rpi4-01")
    display.print_ping(console, client, {"reachable": True, "authorized": False, "detail": "HTTP 401: key mismatch"})
    out = console.export_text()
    assert "http://orch:8080" in out
    assert "rpi4-01" in out
    assert "HTTP 401: key mismatch" in out
    assert "not connected" in out


def test_print_ping_without_url():
    console = _console()
    client = HubClient(url="", api_key="", worker_id="w")
    display.print_ping(console, client, client.ping())
    assert "(not set)" in console.export_text()


def test_print_info_hides_api_key():
    console = _console()
    client = HubClient(url="http://orch:8080", api_key="super-secret", worker_id="w")
    display.print_info(console, {"os": "Linux", "machine": "aarch64"}, client)
    out = console.export_text()
    assert "aarch64" in out
    assert "(set)" in out
    assert "super-secret" not in out


def test_print_run_result_success_and_failure():
    res = {
        "job_id": "job_1", "flow_name": "Demo", "status": "success", "duration_seconds": 1.5,
        "steps_total": 3, "steps_executed": 3, "has_error": False, "error": None,
    }
    console = _console()
    display.print_run_result(console, res)
    out = console.export_text()
    assert "SUCCESS" in out and "3/3" in out and "Error" not in out

    console = _console()
    display.print_run_result(console, {**res, "status": "failed", "has_error": True, "steps_executed": 2,
                                       "error": "Step 'Open' (Timeout): page did not load"})
    out = console.export_text()
    assert "FAILED" in out and "2/3" in out and "page did not load" in out

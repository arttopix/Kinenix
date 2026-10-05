"""The dashboard must never turn worker-provided text into HTML or JavaScript (XSS)."""
import re
import socket
import threading
import time
from pathlib import Path

import pytest

from kinenix_hub import config as hub_config

APP_JS = Path(__file__).resolve().parents[1] / "kinenix_hub" / "static" / "app.js"

# Worker and execution data inside app.js: w (worker), e (execution), s (step), item (execution)
DATA_REF = re.compile(r"\b(w|e|s|item)\.\w+")
SAFE_WRAPPERS = ("escapeHtml(", "osBadge(", "formatTimeAgo(")
CONSTANT_TERNARY = re.compile(r"^[\w.\s=!'\"-]+\?\s*'[^']*'\s*:\s*'[^']*'$")


def _interpolations_in_html_templates(js: str):
    for template in re.finditer(r"`[^`]*`", js):
        body = template.group(0)
        if "<" not in body:
            continue  # plain text templates go to innerText or are escaped where used
        for interp in re.finditer(r"\$\{([^{}]*)\}", body):
            line = js.count("\n", 0, template.start() + interp.start()) + 1
            yield line, interp.group(1).strip()


def test_worker_data_in_html_is_escaped():
    js = APP_JS.read_text(encoding="utf-8")
    unsafe = [
        f"line {line}: ${{{expr}}}"
        for line, expr in _interpolations_in_html_templates(js)
        if DATA_REF.search(expr)
        and not expr.startswith(SAFE_WRAPPERS)
        and not CONSTANT_TERNARY.match(expr)
        and ".toFixed(" not in expr
    ]
    assert unsafe == [], "Wrap worker data in escapeHtml(): " + "; ".join(unsafe)


def test_no_values_inside_inline_event_handlers():
    """onclick="f('${x}')" is unsafe even when escaped: the browser decodes &#39; back to ' before running it."""
    js = APP_JS.read_text(encoding="utf-8")
    assert re.findall(r"on\w+=\"[^\"]*\$\{", js) == []


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PAYLOAD = '<img src=x onerror="window.__xss=1">'


def test_dashboard_shows_malicious_text_without_running_it(monkeypatch):
    """Runs the real dashboard in Chromium when it is installed (skipped in CI)."""
    sync_api = pytest.importorskip("playwright.sync_api")
    uvicorn = pytest.importorskip("uvicorn")
    from fastapi.testclient import TestClient
    from kinenix_hub.app import app

    monkeypatch.setattr(hub_config, "API_KEY", "")
    monkeypatch.setattr(hub_config, "DASHBOARD_PASSWORD", "")
    monkeypatch.setattr(hub_config, "DASHBOARD_PASSWORD_HASH", "")

    local = TestClient(app, client=("127.0.0.1", 50000))
    local.post("/api/v1/heartbeat", json={
        "worker_id": "xss-worker", "name": PAYLOAD, "os_info": PAYLOAD, "ip_address": PAYLOAD,
        "ram_usage": PAYLOAD, "current_task": PAYLOAD,
    })
    local.post("/api/v1/telemetry", json={"worker_id": PAYLOAD, "payload": {
        "flow_name": PAYLOAD, "has_error": True,
        "failure_details": {"failed_step_name": PAYLOAD, "error_message": PAYLOAD},
        "metrics": {"total_duration_seconds": 1.0},
    }})

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)

    try:
        with sync_api.sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                pytest.skip(f"Chromium not available: {e}")
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/", wait_until="domcontentloaded")
            page.wait_for_function("document.querySelector('#workers-container h3') !== null", timeout=10000)
            page.wait_for_function("document.querySelector('#executions-tbody button') !== null", timeout=10000)
            page.wait_for_timeout(500)

            assert page.evaluate("window.__xss") is None, "worker text was executed as HTML"
            assert PAYLOAD in page.inner_text("#workers-container")      # shown as text instead
            assert PAYLOAD in page.inner_text("#executions-tbody")
            assert page.locator("#workers-container img, #executions-tbody img").count() == 0

            page.locator("#executions-tbody button", has_text="ดู Steps").first.click()
            page.wait_for_selector("#steps-modal:not(.hidden)")
            assert page.evaluate("window.__xss") is None
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

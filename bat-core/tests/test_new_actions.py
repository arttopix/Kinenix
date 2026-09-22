import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from batautomate.actions.registry import ActionRegistry
from batautomate.models.context import ExecutionContext
from batautomate.actions.web_playwright import _launch_browser_with_auto_install


# ---------------------------------------------------------
# Action Registration Checks
# ---------------------------------------------------------

def test_new_actions_registered():
    actions = [
        "file.exists",
        "file.copy",
        "file.move",
        "file.delete",
        "csv.read",
        "web.wait_for",
        "web.is_visible",
        "web.get_attribute",
        "web.press",
        "web.scroll",
        "web.hover",
        "web.switch_tab",
    ]
    for act in actions:
        cls = ActionRegistry.get(act)
        assert cls is not None, f"Action '{act}' is not registered in ActionRegistry"


# ---------------------------------------------------------
# File System Actions Tests
# ---------------------------------------------------------

def test_file_exists_action(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("content", encoding="utf-8")

    ctx = ExecutionContext(flow_name="TestFile")
    action_cls = ActionRegistry.get("file.exists")
    action = action_cls()

    # Existing file
    assert action.execute({"path": str(f)}, ctx) is True
    # Non-existing file
    assert action.execute({"path": str(tmp_path / "missing.txt")}, ctx) is False
    # Relative path with __flow_dir__
    ctx.set_variable("__flow_dir__", str(tmp_path))
    assert action.execute({"path": "hello.txt"}, ctx) is True
    assert action.execute({"path": "does_not_exist.txt"}, ctx) is False


def test_file_copy_action(tmp_path):
    src_file = tmp_path / "source.txt"
    src_file.write_text("sample data", encoding="utf-8")
    dst_file = tmp_path / "sub" / "target.txt"

    ctx = ExecutionContext(flow_name="TestFile")
    action_cls = ActionRegistry.get("file.copy")
    action = action_cls()

    # Copy file
    res = action.execute({"source": str(src_file), "destination": str(dst_file)}, ctx)
    assert res["status"] == "copied"
    assert dst_file.exists()
    assert dst_file.read_text(encoding="utf-8") == "sample data"

    # Copy directory
    src_dir = tmp_path / "src_folder"
    src_dir.mkdir()
    (src_dir / "item.txt").write_text("item", encoding="utf-8")
    dst_dir = tmp_path / "dst_folder"

    res = action.execute({"source": str(src_dir), "destination": str(dst_dir)}, ctx)
    assert res["status"] == "copied"
    assert (dst_dir / "item.txt").exists()

    # Overwrite false raises FileExistsError
    with pytest.raises(FileExistsError):
        action.execute({"source": str(src_file), "destination": str(dst_file), "overwrite": False}, ctx)


def test_file_move_action(tmp_path):
    src_file = tmp_path / "to_move.txt"
    src_file.write_text("move me", encoding="utf-8")
    dst_file = tmp_path / "dest" / "moved.txt"

    ctx = ExecutionContext(flow_name="TestFile")
    action_cls = ActionRegistry.get("file.move")
    action = action_cls()

    res = action.execute({"source": str(src_file), "destination": str(dst_file)}, ctx)
    assert res["status"] == "moved"
    assert not src_file.exists()
    assert dst_file.exists()
    assert dst_file.read_text(encoding="utf-8") == "move me"

    # Move non-existent raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        action.execute({"source": str(src_file), "destination": str(dst_file)}, ctx)


def test_file_delete_action(tmp_path):
    f = tmp_path / "delete_me.txt"
    f.write_text("bye", encoding="utf-8")

    d = tmp_path / "delete_folder"
    d.mkdir()
    (d / "inner.txt").write_text("inner", encoding="utf-8")

    ctx = ExecutionContext(flow_name="TestFile")
    action_cls = ActionRegistry.get("file.delete")
    action = action_cls()

    # Delete file
    res = action.execute({"path": str(f)}, ctx)
    assert res["deleted"] is True
    assert not f.exists()

    # Delete folder
    res = action.execute({"path": str(d)}, ctx)
    assert res["deleted"] is True
    assert not d.exists()

    # Missing ok = True
    res = action.execute({"path": str(tmp_path / "none.txt"), "missing_ok": True}, ctx)
    assert res["deleted"] is False

    # Missing ok = False
    with pytest.raises(FileNotFoundError):
        action.execute({"path": str(tmp_path / "none.txt"), "missing_ok": False}, ctx)


# ---------------------------------------------------------
# CSV Read Action Tests
# ---------------------------------------------------------

def test_csv_read_action(tmp_path):
    csv_file = tmp_path / "users.csv"
    csv_file.write_text("name , age , role \nAlice,30,Admin\nBob,25,User", encoding="utf-8")

    ctx = ExecutionContext(flow_name="TestCSV")
    action_cls = ActionRegistry.get("csv.read")
    action = action_cls()

    records = action.execute({"file_path": str(csv_file), "clean_headers": True}, ctx)
    assert len(records) == 2
    assert records[0]["name"] == "Alice"
    assert records[0]["age"] == 30
    assert records[0]["role"] == "Admin"
    assert records[1]["name"] == "Bob"

    # Custom delimiter
    semicolon_file = tmp_path / "items.csv"
    semicolon_file.write_text("sku;price;stock\nA1;99.9;10", encoding="utf-8")
    records2 = action.execute({"file_path": str(semicolon_file), "delimiter": ";"}, ctx)
    assert len(records2) == 1
    assert records2[0]["sku"] == "A1"
    assert records2[0]["stock"] == 10

    # Flow dir resolution
    ctx.set_variable("__flow_dir__", str(tmp_path))
    records3 = action.execute({"file_path": "users.csv"}, ctx)
    assert len(records3) == 2

    # Non-existent file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        action.execute({"file_path": "missing_file.csv"}, ctx)


# ---------------------------------------------------------
# Web Playwright Actions Tests (Mocked)
# ---------------------------------------------------------

def test_web_wait_for():
    page = MagicMock()
    mock_locator = MagicMock()
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.wait_for")
    action = action_cls()

    # With selector
    res = action.execute({"selector": "#submit-btn", "state": "visible", "timeout": 5000}, ctx)
    assert res["status"] == "ready"
    assert res["state"] == "visible"
    page.locator.assert_called_with("#submit-btn")
    mock_locator.first.wait_for.assert_called_with(state="visible", timeout=5000.0)

    # Without selector (pure sleep/wait_for_timeout)
    res2 = action.execute({"timeout": 2000}, ctx)
    assert res2["status"] == "waited"
    assert res2["timeout_ms"] == 2000.0
    page.wait_for_timeout.assert_called_with(2000.0)


def test_web_is_visible():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.is_visible")
    action = action_cls()

    # Case 1: Visible within timeout
    mock_first.wait_for.return_value = None
    assert action.execute({"selector": "button.accept", "timeout": 2000}, ctx) is True
    mock_first.wait_for.assert_called_with(state="visible", timeout=2000.0)

    # Case 2: Not visible (wait_for raises TimeoutError)
    mock_first.wait_for.side_effect = Exception("Timeout 2000ms exceeded")
    assert action.execute({"selector": "button.accept", "timeout": 2000}, ctx) is False

    # Case 3: Immediate check (timeout <= 0)
    mock_first.is_visible.return_value = True
    assert action.execute({"selector": "button.accept", "timeout": 0}, ctx) is True
    mock_first.is_visible.assert_called_once()


def test_web_click_optional():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.click")
    action = action_cls()

    # Successful click with custom timeout
    res = action.execute({"selector": "button#submit", "timeout": 5000}, ctx)
    assert res["status"] == "clicked"
    mock_first.click.assert_called_with(timeout=5000.0)

    # Optional click ignores exception
    mock_first.click.side_effect = Exception("Element not found")
    res_opt = action.execute({"selector": "button#optional", "timeout": 1000, "optional": True}, ctx)
    assert res_opt["status"] == "skipped"
    assert "Element not found" in res_opt["reason"]

    # Non-optional click raises exception
    with pytest.raises(Exception):
        action.execute({"selector": "button#mandatory", "optional": False}, ctx)


def test_web_get_attribute():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_first.get_attribute.return_value = "https://example.com/logo.png"
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.get_attribute")
    action = action_cls()

    val = action.execute({"selector": "img.logo", "attribute": "src"}, ctx)
    assert val == "https://example.com/logo.png"
    mock_first.get_attribute.assert_called_with("src")


def test_web_press():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.press")
    action = action_cls()

    # Key on element
    res = action.execute({"key": "Enter", "selector": "#input-box"}, ctx)
    assert res["status"] == "pressed"
    mock_first.press.assert_called_with("Enter")

    # Global key on page keyboard
    res2 = action.execute({"key": "Escape"}, ctx)
    assert res2["status"] == "pressed"
    page.keyboard.press.assert_called_with("Escape")


def test_web_scroll():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.scroll")
    action = action_cls()

    # Direction down
    res = action.execute({"direction": "down", "amount": 800}, ctx)
    assert res["status"] == "scrolled"
    page.evaluate.assert_called_with("window.scrollBy(0, 800)")

    # Direction bottom
    action.execute({"direction": "bottom"}, ctx)
    page.evaluate.assert_called_with("window.scrollTo(0, document.body.scrollHeight)")

    # Direction top
    action.execute({"direction": "top"}, ctx)
    page.evaluate.assert_called_with("window.scrollTo(0, 0)")

    # Selector scroll into view
    res_elem = action.execute({"selector": "#footer"}, ctx)
    assert res_elem["target"] == "element"
    mock_first.scroll_into_view_if_needed.assert_called_once()


def test_web_hover():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.hover")
    action = action_cls()

    res = action.execute({"selector": ".menu-item", "timeout": 10000}, ctx)
    assert res["status"] == "hovered"
    mock_first.hover.assert_called_with(timeout=10000.0)


def test_web_switch_tab():
    page1 = MagicMock()
    page1.url = "https://example.com/home"
    page1.title.return_value = "Home Page"

    page2 = MagicMock()
    page2.url = "https://example.com/dashboard"
    page2.title.return_value = "User Dashboard"

    browser = MagicMock()
    browser_context = MagicMock()
    browser_context.pages = [page1, page2]
    browser.contexts = [browser_context]

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_browser__", browser)
    ctx.set_variable("__playwright_page__", page1)

    action_cls = ActionRegistry.get("web.switch_tab")
    action = action_cls()

    # Switch by index
    res = action.execute({"index": 1}, ctx)
    assert res["status"] == "switched"
    assert res["title"] == "User Dashboard"
    assert ctx.get_variable("__playwright_page__") == page2
    page2.bring_to_front.assert_called_once()

    # Switch by url_pattern
    res2 = action.execute({"url_pattern": "/home"}, ctx)
    assert res2["status"] == "switched"
    assert ctx.get_variable("__playwright_page__") == page1

    # Switch by title
    res3 = action.execute({"title": "dashboard"}, ctx)
    assert res3["status"] == "switched"
    assert ctx.get_variable("__playwright_page__") == page2

    # Out of range index
    with pytest.raises(IndexError):
        action.execute({"index": 99}, ctx)

    # Missing pattern
    with pytest.raises(ValueError):
        action.execute({"url_pattern": "nonexistent"}, ctx)


def test_headless_auto_fallback():
    pw = MagicMock()
    pw.chromium.launch.side_effect = [
        Exception("Missing X server or $DISPLAY"),
        MagicMock()
    ]

    browser = _launch_browser_with_auto_install(pw, headless=False)
    assert browser is not None
    # Chromium launch was retried with headless=True
    assert pw.chromium.launch.call_count == 2
    assert pw.chromium.launch.call_args_list[1][1] == {"headless": True}

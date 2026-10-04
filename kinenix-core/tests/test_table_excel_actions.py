"""Tests for web.get_table, logic.append (extend), excel.write paths, web.open URL checks, and flow.md error handling."""
import json
from unittest.mock import MagicMock

import pandas as pd
import pytest

from kinenix.actions.registry import ActionRegistry
from kinenix.actions.web_playwright import _TABLE_TO_ROWS_JS
from kinenix.engine.markdown import flow_to_markdown, markdown_to_flow
from kinenix.models.context import ExecutionContext

TABLE = {
    "headers": ["Period", "Buying Rates Sight Bill", "Buying Rates Transfer"],
    "data": [["30 Dec 2024", "33.7514", "33.8296"], ["27 Dec 2024", "1,033.87", "-"]],
}


def _run(action_name, params, ctx):
    return ActionRegistry.get(action_name)().execute(params, ctx)


def _page_ctx(table=TABLE):
    page = MagicMock()
    page.locator.return_value.first.evaluate.return_value = table
    ctx = ExecutionContext(flow_name="TestTable")
    ctx.set_variable("__playwright_page__", page)
    return page, ctx


def test_get_table_returns_rows_keyed_by_header():
    page, ctx = _page_ctx()
    rows = _run("web.get_table", {"selector": "table:visible"}, ctx)
    page.locator.assert_called_with("table:visible")
    assert rows[0] == {"Period": "30 Dec 2024", "Buying Rates Sight Bill": "33.7514", "Buying Rates Transfer": "33.8296"}
    assert len(rows) == 2


def test_get_table_selects_renames_converts_and_adds_columns():
    _, ctx = _page_ctx()
    rows = _run("web.get_table", {
        "selector": "table",
        "columns": {"Period": "Date", "Buying Rates Transfer": "Rate"},
        "numeric_columns": ["Rate"],
        "add_columns": {"Currency": "USD"},
    }, ctx)
    assert rows == [
        {"Currency": "USD", "Date": "30 Dec 2024", "Rate": 33.8296},
        {"Currency": "USD", "Date": "27 Dec 2024", "Rate": None},
    ]
    assert list(rows[0]) == ["Currency", "Date", "Rate"]

    rows = _run("web.get_table", {"selector": "table", "columns": ["Buying Rates Sight Bill"],
                                  "numeric_columns": ["Buying Rates Sight Bill"]}, ctx)
    assert rows[1] == {"Buying Rates Sight Bill": 1033.87}


@pytest.mark.parametrize("params, message", [
    ({"columns": ["Missing"]}, "not found"),
    ({"numeric_columns": ["Period"]}, "not a number"),
    ({"min_rows": 3}, "at least 3"),
    ({"add_columns": ["x"]}, "mapping"),
])
def test_get_table_errors(params, message):
    _, ctx = _page_ctx()
    with pytest.raises(ValueError, match=message):
        _run("web.get_table", {"selector": "table", **params}, ctx)


def test_get_table_script_in_a_real_browser():
    """Runs the table-reading JavaScript in Chromium when it is installed (skipped in CI)."""
    sync_api = pytest.importorskip("playwright.sync_api")
    html = """
      <table id="with-head"><thead><tr><th>Date</th><th> Rate </th></tr></thead>
        <tbody><tr><td>1 Dec</td><td>34.1</td></tr><tr><td></td><td></td></tr><tr><td>2 Dec</td><td>34.2</td></tr></tbody></table>
      <table id="no-head"><tr><td>A</td><td></td></tr><tr><td>1</td><td>2</td></tr></table>
    """
    try:
        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html)
            with_head = page.locator("#with-head").evaluate(_TABLE_TO_ROWS_JS)
            no_head = page.locator("#no-head").evaluate(_TABLE_TO_ROWS_JS)
            browser.close()
    except Exception as e:  # browser not installed
        pytest.skip(f"Chromium not available: {e}")
    assert with_head == {"headers": ["Date", "Rate"], "data": [["1 Dec", "34.1"], ["2 Dec", "34.2"]]}
    assert no_head == {"headers": ["A", "Column 2"], "data": [["1", "2"]]}


def test_append_extend_adds_each_row():
    ctx = ExecutionContext(flow_name="TestAppend")
    _run("logic.append", {"target": "rows", "item": [{"a": 1}, {"a": 2}], "extend": True}, ctx)
    _run("logic.append", {"target": "rows", "item": {"a": 3}}, ctx)
    assert ctx.get_variable("rows") == [{"a": 1}, {"a": 2}, {"a": 3}]
    with pytest.raises(TypeError, match="requires a list"):
        _run("logic.append", {"target": "rows", "item": {"a": 4}, "extend": True}, ctx)


def test_excel_write_resolves_bundle_path_and_orders_columns(tmp_path):
    ctx = ExecutionContext(flow_name="TestExcel")
    ctx.set_variable("__flow_dir__", str(tmp_path))
    res = _run("excel.write", {
        "file_path": "./output/report.xlsx",
        "data": [{"Rate": 1.5, "Currency": "USD"}],
        "sheet_name": "Rates",
        "columns": ["Currency", "Date", "Rate"],
    }, ctx)
    target = tmp_path / "output" / "report.xlsx"
    assert res == {"rows_written": 1, "file_path": str(target)}
    df = pd.read_excel(target, sheet_name="Rates")
    assert list(df.columns) == ["Currency", "Date", "Rate"]
    assert df.loc[0, "Rate"] == 1.5

    with pytest.raises(ValueError, match="file_path"):
        _run("excel.write", {"data": []}, ctx)


def test_web_open_rejects_empty_url():
    ctx = ExecutionContext(flow_name="TestOpen")
    with pytest.raises(ValueError, match="'url' is empty"):
        _run("web.open", {"url": None}, ctx)


def test_flow_md_error_handling_goes_to_error_handler_and_round_trips():
    md = """# Retry Demo

### 1. Open (`web.open`)
- **url:** `${config.url}`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5.0

### 2. Loop (`logic.loop`)
- **items:** `${items}`
- **Sub-steps:**
  - Read (`web.get_table`):
    - **selector:** `table`
    - **on_error:** continue
"""
    flow = markdown_to_flow(md)
    step = flow.steps[0]
    assert step.parameters == {"url": "${config.url}"}
    assert (step.error_handler.on_error, step.error_handler.max_retries, step.error_handler.retry_interval) == ("retry", 2, 5.0)
    child = flow.steps[1].sub_steps[0]
    assert child.parameters == {"selector": "table"}
    assert child.error_handler.on_error == "continue"

    again = markdown_to_flow(flow_to_markdown(flow))
    assert again.model_dump(exclude_none=True) == flow.model_dump(exclude_none=True)


def test_flow_md_error_handler_json_form():
    md = """# Json Form

### 1. Fetch (`http.request`)
- **url:** https://api.example.com
- **error_handler:** {"on_error": "retry", "max_retries": 3, "fallback_step_id": "step_2"}

### 2. Fallback (`logic.delay`)
- **seconds:** 0
"""
    step = markdown_to_flow(md).steps[0]
    assert step.parameters == {"url": "https://api.example.com"}
    assert (step.error_handler.on_error, step.error_handler.max_retries, step.error_handler.fallback_step_id) == ("retry", 3, "step_2")

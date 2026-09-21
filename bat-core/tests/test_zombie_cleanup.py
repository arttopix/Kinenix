import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from batautomate.engine.interpreter import FlowInterpreter
from batautomate.models.flow import FlowDefinition, Step


def test_auto_cleanup_on_flow_failure(tmp_path):
    """
    Verify that when a step fails mid-flow, auto-teardown terminates
    the browser and Playwright instances, leaving no zombie processes.
    """
    bundle_dir = tmp_path / "fail_flow_bundle"
    bundle_dir.mkdir()

    mock_browser = MagicMock()
    mock_browser.is_connected.return_value = True

    mock_pw = MagicMock()
    mock_page = MagicMock()
    mock_page.is_closed.return_value = False

    flow_def = FlowDefinition(
        name="Failing Browser Flow",
        steps=[
            Step(
                id="step_fail",
                name="Failing Action",
                action="excel.read",
                parameters={"file_path": str(bundle_dir / "non_existent.xlsx")}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(bundle_dir),
            "__playwright_browser__": mock_browser,
            "__playwright_page__": mock_page,
            "__playwright_pw__": mock_pw
        }
    )

    assert ctx.has_error is True
    # Auto-cleanup must close the browser and stop playwright
    mock_browser.close.assert_called_once()
    mock_pw.stop.assert_called_once()
    assert ctx.get_variable("__playwright_browser__") is None
    assert ctx.get_variable("__playwright_page__") is None
    assert ctx.get_variable("__playwright_pw__") is None


def test_auto_cleanup_on_missing_web_close(tmp_path):
    """
    Verify that if a flow finishes all steps successfully but the author
    omits a 'web.close' step, the engine automatically tears down the browser.
    """
    bundle_dir = tmp_path / "success_no_close_bundle"
    bundle_dir.mkdir()

    mock_browser = MagicMock()
    mock_browser.is_connected.return_value = True
    mock_pw = MagicMock()

    flow_def = FlowDefinition(
        name="Flow Without Close",
        steps=[
            Step(
                id="step_set",
                name="Set Status",
                action="logic.set_variable",
                parameters={"name": "done", "value": True}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(bundle_dir),
            "__playwright_browser__": mock_browser,
            "__playwright_pw__": mock_pw
        }
    )

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("done") is True

    # Auto-cleanup must close browser even on successful completion
    mock_browser.close.assert_called_once()
    mock_pw.stop.assert_called_once()
    assert ctx.get_variable("__playwright_browser__") is None
    assert ctx.get_variable("__playwright_pw__") is None


def test_subflow_does_not_prematurely_close_parent_browser(tmp_path):
    """
    Verify that when a subflow completes, it does NOT close the browser
    shared from the parent flow. Only the parent root flow closes it.
    """
    parent_bundle = tmp_path / "parent_bundle"
    parent_bundle.mkdir()

    subflow_data = {
        "name": "Child Subflow",
        "steps": [
            Step(
                id="sub_step_1",
                name="Child Set Var",
                action="logic.set_variable",
                parameters={"name": "child_done", "value": True}
            ).model_dump()
        ]
    }
    subflow_path = parent_bundle / "subflow.json"
    subflow_path.write_text(json.dumps(subflow_data), encoding="utf-8")

    mock_browser = MagicMock()
    mock_browser.is_connected.return_value = True
    mock_pw = MagicMock()

    flow_def = FlowDefinition(
        name="Parent Flow",
        steps=[
            Step(
                id="call_child",
                name="Call Subflow",
                action="flow.call",
                parameters={"flow": str(subflow_path)}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(parent_bundle),
            "__playwright_browser__": mock_browser,
            "__playwright_pw__": mock_pw
        }
    )

    assert ctx.is_completed is True
    assert ctx.has_error is False
    # Parent's finally should have called close once upon parent exit, NOT twice from child + parent
    assert mock_browser.close.call_count == 1
    assert mock_pw.stop.call_count == 1


def test_auto_cleanup_disabled_for_studio_sessions(tmp_path):
    """
    Verify that setting auto_close_browser=False keeps the browser session open
    for interactive debugging in Studio.
    """
    bundle_dir = tmp_path / "studio_bundle"
    bundle_dir.mkdir()

    mock_browser = MagicMock()
    mock_pw = MagicMock()

    flow_def = FlowDefinition(
        name="Studio Interactive Step",
        steps=[
            Step(
                id="step_debug",
                name="Debug Step",
                action="logic.set_variable",
                parameters={"name": "step_executed", "value": True}
            )
        ]
    )

    interpreter = FlowInterpreter(auto_close_browser=False)
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(bundle_dir),
            "__playwright_browser__": mock_browser,
            "__playwright_pw__": mock_pw
        }
    )

    assert ctx.is_completed is True
    # Browser should NOT be closed when auto_close_browser is False
    mock_browser.close.assert_not_called()
    mock_pw.stop.assert_not_called()
    assert ctx.get_variable("__playwright_browser__") == mock_browser


def test_auto_cleanup_handles_close_exceptions_gracefully(tmp_path):
    """
    Verify that if browser.close() or pw.stop() raises an error during cleanup,
    it does not swallow or replace the primary flow exception or crash the engine.
    """
    bundle_dir = tmp_path / "error_bundle"
    bundle_dir.mkdir()

    mock_browser = MagicMock()
    mock_browser.close.side_effect = RuntimeError("Process already killed")

    mock_pw = MagicMock()
    mock_pw.stop.side_effect = RuntimeError("Driver communication error")

    flow_def = FlowDefinition(
        name="Flow With Cleanup Exception",
        steps=[
            Step(
                id="step_primary_error",
                name="Primary Failing Step",
                action="excel.read",
                parameters={"file_path": str(bundle_dir / "missing.xlsx")}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(
        flow_def,
        initial_vars={
            "__flow_dir__": str(bundle_dir),
            "__playwright_browser__": mock_browser,
            "__playwright_pw__": mock_pw
        }
    )

    assert ctx.has_error is True
    # Context variables should still be cleared
    assert ctx.get_variable("__playwright_browser__") is None
    assert ctx.get_variable("__playwright_pw__") is None

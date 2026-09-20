from unittest.mock import MagicMock, patch
import pytest

from batautomate.actions.base import BaseAction
from batautomate.actions.registry import ActionRegistry, register_action
from batautomate.engine.interpreter import FlowInterpreter
from batautomate.models.context import ExecutionContext
from batautomate.models.flow import FlowDefinition, Step, ErrorHandlerConfig


# Dummy action for testing transient failures and retries
_mock_attempt_counter = 0

@register_action("test.transient_fail")
class TransientFailAction(BaseAction):
    def execute(self, parameters, context):
        global _mock_attempt_counter
        _mock_attempt_counter += 1
        threshold = parameters.get("fail_until_attempt", 2)
        if _mock_attempt_counter < threshold:
            raise ConnectionError(f"Transient network error on attempt {_mock_attempt_counter}")
        return {"attempt": _mock_attempt_counter, "status": "success"}


def test_step_retry_success():
    global _mock_attempt_counter
    _mock_attempt_counter = 0

    flow = FlowDefinition(
        name="Test Retry Success",
        steps=[
            Step(
                id="step_flaky",
                name="Flaky Network Call",
                action="test.transient_fail",
                parameters={"fail_until_attempt": 3},
                output_var="flaky_result",
                error_handler=ErrorHandlerConfig(
                    on_error="retry",
                    max_retries=3,
                    retry_interval=0.01
                )
            ),
            Step(
                id="step_next",
                name="Next Step",
                action="logic.set_variable",
                parameters={"name": "finished", "value": True}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("flaky_result")["status"] == "success"
    assert ctx.get_variable("finished") is True
    assert _mock_attempt_counter == 3


def test_step_retry_exhausted():
    global _mock_attempt_counter
    _mock_attempt_counter = 0

    flow = FlowDefinition(
        name="Test Retry Exhausted",
        steps=[
            Step(
                id="step_impossible",
                name="Always Fails",
                action="test.transient_fail",
                parameters={"fail_until_attempt": 99},
                error_handler=ErrorHandlerConfig(
                    on_error="retry",
                    max_retries=2,
                    retry_interval=0.01
                )
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is False
    assert ctx.has_error is True
    assert ctx.failure_details is not None
    assert ctx.failure_details.failed_step_id == "step_impossible"
    # 1 original + 2 retries = 3 attempts total
    assert _mock_attempt_counter == 3


def test_step_fallback_execution_and_continuation():
    flow = FlowDefinition(
        name="Test Fallback",
        steps=[
            Step(
                id="step_primary",
                name="Primary Failing Step",
                action="test.transient_fail",
                parameters={"fail_until_attempt": 999},
                error_handler=ErrorHandlerConfig(
                    on_error="stop",
                    fallback_step_id="step_recovery"
                )
            ),
            Step(
                id="step_subsequent",
                name="Subsequent Normal Step",
                action="logic.set_variable",
                parameters={"name": "flow_finished", "value": True}
            ),
            Step(
                id="step_recovery",
                name="Recovery Step",
                action="logic.set_variable",
                parameters={"name": "recovered_by_fallback", "value": True}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    assert ctx.get_variable("recovered_by_fallback") is True
    assert ctx.get_variable("flow_finished") is True


def test_missing_fallback_step_validation():
    flow = FlowDefinition(
        name="Test Invalid Fallback",
        steps=[
            Step(
                id="step_main",
                name="Main Step",
                action="logic.set_variable",
                parameters={"name": "x", "value": 1},
                error_handler=ErrorHandlerConfig(
                    fallback_step_id="non_existent_step_id"
                )
            )
        ]
    )

    interpreter = FlowInterpreter()
    with pytest.raises(ValueError, match="non_existent_step_id"):
        interpreter.run_flow(flow)


def test_on_error_continue():
    flow = FlowDefinition(
        name="Test Continue",
        steps=[
            Step(
                id="step_fail_continue",
                name="Fails But Continues",
                action="test.transient_fail",
                parameters={"fail_until_attempt": 999},
                error_handler=ErrorHandlerConfig(
                    on_error="continue"
                )
            ),
            Step(
                id="step_after",
                name="Step After",
                action="logic.set_variable",
                parameters={"name": "reached_after", "value": True}
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.get_variable("reached_after") is True
    assert ctx.metrics.failed_steps == 1


# ---------------------------------------------------------
# Web Form Actions Tests
# ---------------------------------------------------------

def test_web_select_option():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_first.select_option.return_value = ["TH"]
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.select_option")
    action = action_cls()

    # By value
    res = action.execute({"selector": "#country-select", "value": "TH"}, ctx)
    assert res["status"] == "selected"
    assert res["selected"] == ["TH"]
    mock_first.select_option.assert_called_with(value="TH")

    # By text/label
    action.execute({"selector": "#country-select", "text": "Thailand"}, ctx)
    mock_first.select_option.assert_called_with(label="Thailand")

    # By index
    action.execute({"selector": "#country-select", "index": 2}, ctx)
    mock_first.select_option.assert_called_with(index=2)


def test_web_upload_file(tmp_path):
    f = tmp_path / "invoice.pdf"
    f.write_text("dummy pdf", encoding="utf-8")

    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    action_cls = ActionRegistry.get("web.upload_file")
    action = action_cls()

    res = action.execute({"selector": "input[type='file']", "file_path": str(f)}, ctx)
    assert res["status"] == "uploaded"
    assert res["file_path"] == str(f.resolve())
    mock_first.set_input_files.assert_called_with(str(f.resolve()))

    # Missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        action.execute({"selector": "input[type='file']", "file_path": str(tmp_path / "missing.pdf")}, ctx)


def test_web_check_and_uncheck():
    page = MagicMock()
    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first
    page.locator.return_value = mock_locator

    ctx = ExecutionContext(flow_name="TestWeb")
    ctx.set_variable("__playwright_page__", page)

    check_action = ActionRegistry.get("web.check")()
    res_check = check_action.execute({"selector": "#agree-terms"}, ctx)
    assert res_check["status"] == "checked"
    mock_first.check.assert_called_with(timeout=30000.0)

    uncheck_action = ActionRegistry.get("web.uncheck")()
    res_uncheck = uncheck_action.execute({"selector": "#newsletter"}, ctx)
    assert res_uncheck["status"] == "unchecked"
    mock_first.uncheck.assert_called_with(timeout=30000.0)

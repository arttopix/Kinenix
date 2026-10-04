from unittest.mock import MagicMock

import pytest

from kinenix.actions.flow_control import BusinessRuleError, FlowFailedError
from kinenix.actions.registry import ActionRegistry
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import markdown_to_flow
from kinenix.models.context import ExecutionContext


def _run(action_name, params, ctx):
    return ActionRegistry.get(action_name)().execute(params, ctx)


def test_flow_fail_categories():
    ctx = ExecutionContext(flow_name="Fail")
    with pytest.raises(BusinessRuleError, match="No rates for SGD"):
        _run("flow.fail", {"message": "No rates for SGD"}, ctx)
    with pytest.raises(FlowFailedError, match="Portal down"):
        _run("flow.fail", {"message": "Portal down", "category": "technical"}, ctx)
    with pytest.raises(ValueError, match="category"):
        _run("flow.fail", {"message": "x", "category": "other"}, ctx)


def test_business_failure_is_recorded_and_not_retried(tmp_path):
    flow = markdown_to_flow("""# Business Stop

## Variables
- `rows`: []

### 1. Stop When No Data (`flow.fail`)
- **condition:** `${rows} == []`
- **message:** No exchange rates were found for the requested period
- **on_error:** retry
- **max_retries:** 3
- **retry_interval:** 5.0

### 2. Never Reached (`logic.set_variable`)
- **name:** reached
- **value:** true
""")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(tmp_path)})
    assert ctx.has_error
    details = ctx.failure_details
    assert details.error_type == "Business"
    assert details.exception_class == "BusinessRuleError"
    assert details.error_message == "No exchange rates were found for the requested period"
    # Not retried: one attempt only, so the 5 second retry interval was never slept
    assert [r.status for r in ctx.step_results] == ["failed"]
    assert ctx.get_variable("reached") is None


def test_condition_false_skips_flow_fail(tmp_path):
    flow = markdown_to_flow("""# Has Data

## Variables
- `rows`: [1]

### 1. Stop When No Data (`flow.fail`)
- **condition:** `${rows} == []`
- **message:** empty
""")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(tmp_path)})
    assert not ctx.has_error


def _click_ctx():
    page = MagicMock()
    response = MagicMock(url="https://site/api/results.json", status=200)
    page.expect_response.return_value.__enter__.return_value = MagicMock(value=response)
    ctx = ExecutionContext(flow_name="Click")
    ctx.set_variable("__playwright_page__", page)
    return page, ctx


def test_click_waits_for_matching_response():
    page, ctx = _click_ctx()
    res = _run("web.click", {"selector": "button.go", "wait_for_response": "results",
                             "response_timeout": 20000}, ctx)
    assert res == {"action": "web.click", "status": "clicked",
                   "response_url": "https://site/api/results.json", "response_status": 200}
    predicate = page.expect_response.call_args.args[0]
    assert page.expect_response.call_args.kwargs["timeout"] == 20000.0
    assert predicate(MagicMock(url="https://site/api/results.json"))
    assert not predicate(MagicMock(url="https://site/analytics"))
    page.locator.return_value.first.click.assert_called_once()


def test_click_without_wait_does_not_expect_response():
    page, ctx = _click_ctx()
    assert _run("web.click", {"selector": "button"}, ctx) == {"action": "web.click", "status": "clicked"}
    page.expect_response.assert_not_called()


def test_optional_click_with_wait_is_skipped_on_timeout():
    page, ctx = _click_ctx()
    page.expect_response.return_value.__enter__.side_effect = TimeoutError("no response")
    res = _run("web.click", {"selector": "button", "wait_for_response": "x", "optional": True}, ctx)
    assert res["status"] == "skipped"

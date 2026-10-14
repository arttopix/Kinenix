"""Phase 2 PR 5a (#54, #62): one record per run with every step, failure facts, work items, and a live log."""
import json
from unittest.mock import MagicMock, patch

from kinenix import __version__
from kinenix.actions.flow_control import SubflowExecutionError
from kinenix.engine.interpreter import FlowInterpreter, new_run_id
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.redaction import Redactor
from kinenix.models.context import ExecutionContext, FailureDetails
from kinenix.models.flow import Step

REQUESTS = [{"request_id": "R1", "brand": "TOYOTA"}, {"request_id": "R2", "brand": "HONDA"},
            {"request_id": "R3", "brand": "MAZDA"}]

CHILD = """# process_one

## Steps

### 1. Choose Brand (`flow.fail`)
- **condition:** ${req.brand} == HONDA
- **message:** no option for ${req.brand}

### 2. Save (`file.write_text`)
- **path:** ./output/${req.request_id}.txt
- **content:** ok
"""

PARENT = """# TIPH Quotes

## Steps

### 1. Each Request (`logic.loop`)
- **items:** ${config.requests}
- **item_var:** req
- **item_label:** ${req.request_id} ${req.brand}
- **Sub-steps:**
  - Process One (`flow.call`):
    - **flow:** ./subflows/process_one.md
    - **inputs:** {"req": "${req}"}
    - **on_error:** continue

### 2. Attach Log (`file.read_text`)
- **path:** ${run.log_path}
- **output_var:** log_so_far
"""


def make_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "subflows").mkdir(parents=True)
    (bundle / "subflows" / "process_one.md").write_text(CHILD, encoding="utf-8")
    return bundle


def run(tmp_path, markdown, bundle, **initial):
    logger = ExecutionLogger(log_dir=tmp_path / "logs")
    ctx = FlowInterpreter(logger=logger).run_flow(
        markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(bundle), **initial})
    return ctx


def test_one_run_one_log_with_every_subflow_step_and_one_telemetry_post(tmp_path, monkeypatch):
    monkeypatch.setenv("KINENIX_HUB_URL", "http://hub:8080")
    monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    bundle = make_bundle(tmp_path)
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        ctx = run(tmp_path, PARENT, bundle, config={"requests": REQUESTS})

    assert not ctx.has_error, ctx.failure_details
    assert mock_post.call_count == 1  # subflows used to send a run of their own each
    logs = list((tmp_path / "logs").rglob("*.json"))
    assert len(logs) == 1
    log = json.loads(logs[0].read_text(encoding="utf-8"))
    assert log["run_id"] == ctx.run_id and log["kinenix_version"] == __version__
    child_steps = [s for s in log["step_results"] if s["subflow"] == "process_one"]
    assert [s["step_name"] for s in child_steps] == ["Choose Brand", "Save", "Choose Brand", "Choose Brand", "Save"]
    assert child_steps[0]["path"] == "TIPH Quotes > Each Request > process_one > Choose Brand"
    assert child_steps[0]["line"] == 5
    assert child_steps[2]["loop"] == {"index": 2, "of": 3, "item": "R2 HONDA"}


def test_failures_record_how_they_were_handled_and_items_are_counted(tmp_path):
    bundle = make_bundle(tmp_path)
    ctx = run(tmp_path, PARENT, bundle, config={"requests": REQUESTS})
    failed = [r for r in ctx.step_results if r.status == "failed"]
    inner = next(r for r in failed if r.subflow == "process_one")
    call = next(r for r in failed if r.action == "flow.call")
    # The subflow stopped at Choose Brand; the caller continued with the next request
    assert inner.failure["handled"] == "continued" and inner.failure["from_subflow"] is False
    assert inner.failure["exception"] == "BusinessRuleError" and inner.failure["root_cause"]
    assert call.failure["from_subflow"] is True
    assert ctx.items == {"total": 3, "done": 2, "failed": 1}


def test_a_stopping_failure_counts_the_item_and_leaves_the_rest_not_reached(tmp_path):
    bundle = make_bundle(tmp_path)
    stopping = PARENT.replace("    - **on_error:** continue\n", "")
    ctx = run(tmp_path, stopping, bundle, config={"requests": REQUESTS})
    assert ctx.has_error
    inner = next(r for r in ctx.step_results if r.status == "failed" and r.subflow)
    assert inner.failure["handled"] == "stopped"
    assert ctx.items == {"total": 3, "done": 1, "failed": 1}  # R3 was not reached


def test_the_live_log_has_one_line_per_step_so_far(tmp_path):
    bundle = make_bundle(tmp_path)
    ctx = run(tmp_path, PARENT, bundle, config={"requests": REQUESTS})
    live = ctx.variables["run"]["log_path"]
    assert live.endswith(f"_{ctx.run_id}.jsonl")
    lines_when_read = ctx.variables["log_so_far"]["content"].strip().splitlines() \
        if isinstance(ctx.variables["log_so_far"], dict) else str(ctx.variables["log_so_far"]).strip().splitlines()
    # Attach Log read the file before its own line was written
    assert len(lines_when_read) == len(ctx.step_results) - 1
    with open(live, encoding="utf-8") as f:
        assert [json.loads(line)["step_id"] for line in f] == [r.step_id for r in ctx.step_results]


def test_continued_and_fallback_failures_are_recorded(tmp_path):
    md = """# Handled

## Steps

### 1. Optional (`file.read_text`)
- **path:** ./a.txt
- **on_error:** continue

### 2. With Fallback (`file.read_text`)
- **path:** ./b.txt
- **fallback_step_id:** recover

### recover. Recover (`file.write_text`)
- **path:** ./output/recovered.txt
- **content:** ok
"""
    ctx = run(tmp_path, md, tmp_path)
    handled = {r.step_id: r.failure["handled"] for r in ctx.step_results if r.failure}
    assert handled == {"step_1": "continued", "step_2": "fallback"}
    assert all(r.retries == 0 for r in ctx.step_results)


def test_a_failed_subflow_reuses_its_screenshot_instead_of_taking_another(tmp_path):
    interpreter = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs"))
    child = ExecutionContext(flow_name="child")
    child.failure_details = FailureDetails(failed_step_id="s1", failed_step_name="Click", action="web.click",
                                           exception_class="TimeoutError", error_message="timeout",
                                           root_cause="x", suggested_fix="y", error_screenshot_path="/shots/one.png")
    exc = SubflowExecutionError("Subflow 'child' failed", subflow_name="child", child_context=child)

    def no_second_shot(*args, **kwargs):
        raise AssertionError("a second screenshot was taken")

    interpreter._try_capture_failure_screenshot = no_second_shot
    step = Step(id="step_1", name="Call", action="flow.call")
    diag = interpreter._diagnose_failure(step, exc, ExecutionContext(flow_name="parent"))
    assert diag.error_screenshot_path == "/shots/one.png"


def test_run_ids_are_never_mistaken_for_card_numbers():
    # 20261014-054855-43ac was hidden as [card]ac in CI, and 060049-5345 would read as a phone number
    from datetime import datetime, timedelta
    redactor = Redactor()
    start = datetime(2026, 10, 14, 5, 48, 55)
    for second in range(0, 86400 * 3, 7):
        run_id = new_run_id(start + timedelta(seconds=second))
        assert redactor.redact(run_id) == run_id

"""Phase 2 PR 4 (#50, #51, #52): ## On Error, ## Finally, ${error}, ${run}, item_label, retries then on_error."""
import logging

from kinenix.engine import requires
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import flow_to_markdown, markdown_to_flow
from kinenix.engine.requires import requirement_problem, version_key
from kinenix.engine.validation import validate_flow

FAIL_STEP = """### {n}. Read Missing (`file.read_text`)
- **path:** ./missing/nothing.txt
"""

REPORT = "${error.step_name}|${error.line}|${error.retries}|${error.section}|${error.path}|${error.type}|${run.status}"


def write_step(n, path, content):
    return f"""### {n}. Write {path} (`file.write_text`)
- **path:** ./output/{path}
- **content:** {content}
"""


def run(tmp_path, markdown, **initial):
    bundle = tmp_path / "bundle"
    bundle.mkdir(exist_ok=True)
    ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
        markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(bundle), **initial})
    return ctx, bundle


def read(bundle, name):
    path = bundle / "output" / name
    return path.read_text(encoding="utf-8") if path.exists() else None


FLOW = """# Report Flow
> Requires: kinenix>=0.2.0b4

## Steps

{steps}
## On Error

### 1. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** """ + REPORT + """

## Finally

### 1. Done (`file.write_text`)
- **path:** ./output/finally.txt
- **content:** ${run.status}
"""


def test_sections_are_parsed_with_ids_lines_and_requires_and_exported():
    flow = markdown_to_flow(FLOW.replace("{steps}", FAIL_STEP.format(n=1)))
    assert flow.requires == "kinenix>=0.2.0b4"
    assert [(s.id, s.line) for s in flow.steps] == [("step_1", 6)]
    assert [(s.id, s.line) for s in flow.on_error_steps] == [("on_error_1", 11)]
    assert [(s.id, s.line) for s in flow.finally_steps] == [("finally_1", 17)]
    exported = flow_to_markdown(flow)
    assert "> Requires: kinenix>=0.2.0b4" in exported
    assert "## On Error\n\n### 1. Report (`file.write_text`)" in exported
    assert markdown_to_flow(exported).model_dump() == flow.model_dump()


def test_on_error_runs_when_steps_fail_and_finally_always_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(requires, "__version__", "0.2.0b4")
    steps = write_step(1, "first.txt", "ok") + "\n" + FAIL_STEP.format(n=2) + "\n" + write_step(3, "never.txt", "x")
    ctx, bundle = run(tmp_path, FLOW.replace("{steps}", steps))
    assert ctx.has_error and not ctx.is_completed
    assert read(bundle, "first.txt") == "ok" and read(bundle, "never.txt") is None
    assert read(bundle, "error.txt") == "Read Missing|10|0|steps|Report Flow > Read Missing|Technical|failed"
    assert read(bundle, "finally.txt") == "failed"
    assert ctx.failure_details.failed_step_id == "step_2"
    assert ctx.failure_details.section == "steps"
    assert [r.section for r in ctx.step_results] == ["steps", "steps", "on_error", "finally"]


def test_a_successful_run_skips_on_error(tmp_path, monkeypatch):
    monkeypatch.setattr(requires, "__version__", "0.2.0b4")
    ctx, bundle = run(tmp_path, FLOW.replace("{steps}", write_step(1, "first.txt", "${run.id}")))
    assert not ctx.has_error and ctx.is_completed
    assert read(bundle, "error.txt") is None
    assert read(bundle, "finally.txt") == "success"
    assert read(bundle, "first.txt") == ctx.variables["run"]["id"]


def test_retries_come_first_then_on_error_continue(tmp_path):
    # Before #52, max_retries only worked with on_error: retry
    md = """# Retry Then Continue

## Steps

### 1. Read Missing (`file.read_text`)
- **path:** ./missing.txt
- **max_retries:** ${config.tries}
- **retry_interval:** 0
- **on_error:** continue

### 2. After (`file.write_text`)
- **path:** ./output/after.txt
- **content:** ${error.retries} retries, then ${error.step_name}
"""
    ctx, bundle = run(tmp_path, md, config={"tries": 2})
    assert not ctx.has_error
    assert read(bundle, "after.txt") == "2 retries, then Read Missing"
    assert [r.status for r in ctx.step_results] == ["failed", "success"]


def test_a_stopping_failure_after_a_continued_one_is_the_runs_failure(tmp_path):
    md = """# Two Failures

## Steps

### 1. Optional (`file.read_text`)
- **path:** ./a.txt
- **on_error:** continue

### 2. Required (`file.read_text`)
- **path:** ./b.txt
"""
    ctx, _ = run(tmp_path, md)
    assert ctx.has_error
    assert ctx.failure_details.failed_step_id == "step_2"


def test_a_failure_inside_on_error_is_recorded_and_the_section_goes_on(tmp_path):
    md = """# Broken Handler

## Steps

### 1. Read Missing (`file.read_text`)
- **path:** ./missing.txt

## On Error

### 1. Also Broken (`file.read_text`)
- **path:** ./missing-too.txt

### 2. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** ${error.step_name}
"""
    ctx, bundle = run(tmp_path, md)
    assert ctx.has_error
    assert read(bundle, "error.txt") == "Read Missing"
    assert ctx.failure_details.failed_step_id == "step_1"
    assert [(r.step_id, r.status) for r in ctx.step_results] == [
        ("step_1", "failed"), ("on_error_1", "failed"), ("on_error_2", "success")]


def test_a_failure_in_finally_fails_a_successful_run_and_the_log_says_finally(tmp_path, caplog):
    md = """# Broken Finally

## Steps

### 1. Fine (`file.write_text`)
- **path:** ./output/fine.txt
- **content:** ok

## On Error

### 1. Must Not Run (`file.write_text`)
- **path:** ./output/error.txt
- **content:** x

## Finally

### 1. Zip Missing (`file.read_text`)
- **path:** ./missing.txt

### 2. Still Runs (`file.write_text`)
- **path:** ./output/finally.txt
- **content:** done
"""
    with caplog.at_level(logging.INFO, logger="kinenix"):
        ctx, bundle = run(tmp_path, md)
    assert ctx.has_error and not ctx.is_completed
    assert ctx.failure_details.failed_step_id == "finally_1"
    assert ctx.failure_details.section == "finally"
    assert read(bundle, "error.txt") is None
    assert read(bundle, "finally.txt") == "done"
    assert ctx.variables["run"]["status"] == "failed"
    assert "Failed Step [finally_1] 'Zip Missing' in Finally" in caplog.text
    assert "Result: FAILED at step [finally_1] 'Zip Missing' in Finally" in caplog.text


def test_flow_return_does_not_skip_finally(tmp_path):
    md = """# Early Exit

## Steps

### 1. Stop Here (`flow.return`)
- **value:** done

### 2. Never (`file.write_text`)
- **path:** ./output/never.txt
- **content:** x

## Finally

### 1. Close (`file.write_text`)
- **path:** ./output/finally.txt
- **content:** closed
"""
    ctx, bundle = run(tmp_path, md)
    assert not ctx.has_error
    assert read(bundle, "never.txt") is None
    assert read(bundle, "finally.txt") == "closed"


def test_a_business_failure_runs_on_error_with_type_business(tmp_path):
    md = """# Business

## Steps

### 1. No Quote (`flow.fail`)
- **message:** No quote for this car

## On Error

### 1. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** ${error.type}: ${error.message}
"""
    ctx, bundle = run(tmp_path, md)
    assert ctx.has_error
    assert read(bundle, "error.txt") == "Business: No quote for this car"


LOOP = """# Loop Flow

## Steps

### 1. Each Request (`logic.loop`)
- **items:** ${config.requests}
- **item_var:** req
{label}- **Sub-steps:**
  - Fail On Honda (`flow.fail`):
    - **condition:** ${req.brand} == HONDA
    - **message:** no quote

## On Error

### 1. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** ${error.loop.item}|${error.loop.index}|${error.loop.of}|${error.path}
"""

REQUESTS = [
    {"request_id": "R1", "brand": "TOYOTA", "model": "Yaris", "note": "a"},
    {"request_id": "R2", "brand": "HONDA", "model": "HR-V", "note": "b"},
    {"request_id": "R3", "brand": "MAZDA", "model": "2", "note": "c"},
]


def test_loop_items_are_named_by_item_label(tmp_path):
    md = LOOP.replace("{label}", "- **item_label:** ${req.request_id} ${req.model}\n")
    ctx, bundle = run(tmp_path, md, config={"requests": REQUESTS})
    assert ctx.has_error
    assert read(bundle, "error.txt") == "R2 HR-V|2|3|Loop Flow > Each Request > Fail On Honda"


def test_loop_items_without_item_label_use_their_first_three_fields(tmp_path):
    ctx, bundle = run(tmp_path, LOOP.replace("{label}", ""), config={"requests": REQUESTS})
    assert read(bundle, "error.txt").startswith("R2 HONDA HR-V|2|3|")


def test_a_subflow_failure_reaches_the_caller_with_the_inner_step_and_path(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "subflows").mkdir(parents=True)
    (bundle / "subflows" / "process_one.md").write_text("""# process_one

## Steps

### 1. Choose Brand (`flow.fail`)
- **message:** no option for ${req.brand}

## On Error

### 1. Child Report (`file.write_text`)
- **path:** ./output/child_error.txt
- **content:** ${error.step_name} in ${error.subflow}

## Finally

### 1. Child Finally (`file.write_text`)
- **path:** ./output/child_finally.txt
- **content:** ${run.id}
""", encoding="utf-8")
    md = """# TIPH Quotes

## Steps

### 1. Each Request (`logic.loop`)
- **items:** ${config.requests}
- **item_var:** req
- **item_label:** ${req.request_id}
- **Sub-steps:**
  - Process One (`flow.call`):
    - **flow:** ./subflows/process_one.md
    - **inputs:** {"req": "${req}"}

## On Error

### 1. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** ${error.path}|${error.subflow}|${error.step_name}|${error.line}|${error.loop.item}|${error.message}
"""
    ctx, _ = run(tmp_path, md, config={"requests": REQUESTS[1:]})
    assert ctx.has_error
    assert read(bundle, "child_error.txt") == "Choose Brand in process_one"
    assert read(bundle, "child_finally.txt") == ctx.variables["run"]["id"]
    assert read(bundle, "error.txt") == (
        "TIPH Quotes > Each Request > process_one > Choose Brand|process_one|Choose Brand|5|R2|no option for HONDA")


def test_error_fields_are_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("KX_TEST_PORTAL_TOKEN", "tok-4455-secret")
    md = """# Redacted Error

## Steps

### 1. Read (`file.read_text`)
- **path:** ./missing/${env.KX_TEST_PORTAL_TOKEN}.txt

## On Error

### 1. Report (`file.write_text`)
- **path:** ./output/error.txt
- **content:** ${error.message}
"""
    ctx, bundle = run(tmp_path, md)
    text = read(bundle, "error.txt")
    assert "tok-4455-secret" not in text and "****" in text


def test_versions_and_requirements():
    assert version_key("0.2.0b3") < version_key("0.2.0b4") < version_key("0.2.0rc1") < version_key("0.2.0")
    assert version_key("0.2.0.dev1") < version_key("0.2.0") < version_key("0.2.1") < version_key("1.0")
    assert requirement_problem("kinenix>=0.2.0b4", "0.2.0b4") is None
    assert requirement_problem("kinenix>=0.2.0b4, <1.0", "0.3.0") is None
    assert "runs Kinenix 0.2.0b3" in requirement_problem("kinenix>=0.2.0b4", "0.2.0b3")
    assert "not understood" in requirement_problem("python>=3.10", "0.2.0b4")


def test_an_old_kinenix_refuses_the_flow_without_running_anything(tmp_path, monkeypatch):
    monkeypatch.setattr(requires, "__version__", "0.2.0b3")
    ctx, bundle = run(tmp_path, FLOW.replace("{steps}", write_step(1, "first.txt", "ok")))
    assert ctx.has_error
    assert ctx.failure_details.failed_step_id == "flow_requires"
    assert ctx.step_results == []
    assert read(bundle, "first.txt") is None and read(bundle, "finally.txt") is None


def test_validate_asks_for_requires_and_checks_on_error_values(monkeypatch):
    monkeypatch.setattr(requires, "__version__", "0.2.0b4")
    without = FLOW.replace("{steps}", FAIL_STEP.format(n=1)).replace("> Requires: kinenix>=0.2.0b4\n", "")
    issues = validate_flow(markdown_to_flow(without))
    assert any("## On Error, ## Finally" in i and "> Requires: kinenix>=0.2.0b4" in i for i in issues)
    assert validate_flow(markdown_to_flow(FLOW.replace("{steps}", FAIL_STEP.format(n=1)))) == []
    typo = "# T\n\n## Steps\n\n### 1. Read (`file.read_text`)\n- **path:** ./a.txt\n- **on_error:** skip\n"
    assert any("on_error 'skip'" in i for i in validate_flow(markdown_to_flow(typo)))

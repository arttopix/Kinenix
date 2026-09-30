import json
import pytest
from pathlib import Path

from kinenix.models.flow import FlowDefinition, Step
from kinenix.engine.markdown import (
    flow_to_markdown,
    markdown_to_flow,
    load_flow,
    compile_markdown_to_json,
    export_json_to_markdown,
)


def test_markdown_to_flow_basic():
    md = """# My Test Flow
> Description: Automate sample website login
> Version: 1.2.0

## Variables
- `login_url`: https://example.com/login
- `retry_count`: 3
- `is_active`: true

## Steps

### 1. Open Website (`web.open`)
- **url:** ${login_url}
- **headless:** true

### 2. Enter Username (`web.type`)
- **selector:** #username
- **text:** admin
- **output_var:** `last_status`
"""
    flow = markdown_to_flow(md)
    assert flow.name == "My Test Flow"
    assert flow.description == "Automate sample website login"
    assert flow.version == "1.2.0"
    assert flow.variables["login_url"] == "https://example.com/login"
    assert flow.variables["retry_count"] == 3
    assert flow.variables["is_active"] is True

    assert len(flow.steps) == 2
    assert flow.steps[0].id == "step_1"
    assert flow.steps[0].name == "Open Website"
    assert flow.steps[0].action == "web.open"
    assert flow.steps[0].parameters["url"] == "${login_url}"
    assert flow.steps[0].parameters["headless"] is True

    assert flow.steps[1].id == "step_2"
    assert flow.steps[1].name == "Enter Username"
    assert flow.steps[1].action == "web.type"
    assert flow.steps[1].parameters["selector"] == "#username"
    assert flow.steps[1].parameters["text"] == "admin"
    assert flow.steps[1].output_var == "last_status"


def test_nested_sub_steps_and_else():
    md = """# Nested Flow
> Description: Flow with loops and conditions
> Version: 1.0.0

## Steps

### 1. Loop Records (`logic.loop`)
- **items:** ${records}
- **item_var:** row
- **Sub-steps:**
  - Check Status (`logic.if`):
    - **condition:** ${row.status} == 'OK'
    - **Sub-steps:**
      - Process Row (`web.type`):
        - **text:** ${row.name}
    - **Else-steps:**
      - Log Warning (`logic.append`):
        - **target:** errors
        - **item:** ${row.name}
"""
    flow = markdown_to_flow(md)
    assert len(flow.steps) == 1
    step_1 = flow.steps[0]
    assert step_1.action == "logic.loop"
    assert step_1.sub_steps is not None
    assert len(step_1.sub_steps) == 1

    if_step = step_1.sub_steps[0]
    assert if_step.action == "logic.if"
    assert if_step.condition == "${row.status} == 'OK'"
    assert if_step.sub_steps is not None
    assert len(if_step.sub_steps) == 1
    assert if_step.sub_steps[0].action == "web.type"
    assert if_step.sub_steps[0].parameters["text"] == "${row.name}"

    assert if_step.else_steps is not None
    assert len(if_step.else_steps) == 1
    assert if_step.else_steps[0].action == "logic.append"
    assert if_step.else_steps[0].parameters["target"] == "errors"


def test_roundtrip_equality():
    flow = FlowDefinition(
        name="Roundtrip Test",
        description="Verify roundtrip serialization",
        version="2.0.0",
        variables={"count": 5, "flag": False},
        steps=[
            Step(
                id="step_1",
                name="Start Step",
                action="logic.delay",
                parameters={"seconds": 1.5},
            ),
            Step(
                id="step_2",
                name="Call API",
                action="http.request",
                parameters={"url": "https://api.example.com", "method": "GET"},
                output_var="api_response",
            ),
        ],
    )

    md_text = flow_to_markdown(flow)
    reloaded_flow = markdown_to_flow(md_text)

    assert reloaded_flow.name == flow.name
    assert reloaded_flow.description == flow.description
    assert reloaded_flow.version == flow.version
    assert reloaded_flow.variables == flow.variables
    assert len(reloaded_flow.steps) == len(flow.steps)
    assert reloaded_flow.steps[0].action == flow.steps[0].action
    assert reloaded_flow.steps[0].parameters == flow.steps[0].parameters
    assert reloaded_flow.steps[1].output_var == flow.steps[1].output_var


def test_parse_rpachallenge_flow_md():
    md_path = Path(__file__).resolve().parent.parent.parent / "flows" / "examples" / "rpachallenge" / "flow.md"
    assert md_path.exists(), f"Missing reference flow.md at {md_path}"

    flow = load_flow(md_path)
    assert flow.name == "RPA Challenge Solver"
    assert flow.version == "1.0.0"
    assert "non_programmers" in flow.variables
    assert len(flow.steps) >= 6

    # Step 1: web.open
    assert flow.steps[0].action == "web.open"
    assert flow.steps[0].parameters["url"] == "${config.website}"
    assert flow.steps[0].parameters["headless"] is False

    # Step 4: logic.loop with nested logic.if
    loop_step = flow.steps[3]
    assert loop_step.action == "logic.loop"
    assert loop_step.sub_steps is not None
    assert len(loop_step.sub_steps) == 1  # logic.if

    if_step = loop_step.sub_steps[0]
    assert if_step.action == "logic.if"
    assert if_step.parameters["operator"] == "equals"
    assert if_step.sub_steps is not None
    assert len(if_step.sub_steps) == 8  # 7 web.type fields + Submit button
    assert if_step.else_steps is not None
    assert len(if_step.else_steps) == 1  # logic.append


def test_compile_and_export_cli_functions(tmp_path):
    sample_md = """# CLI Test
> Description: Testing CLI compilation
> Version: 1.0.0

## Steps

### 1. Delay Step (`logic.delay`)
- **seconds:** 1
"""
    md_file = tmp_path / "flow.md"
    md_file.write_text(sample_md, encoding="utf-8")

    # Compile to JSON
    json_out = compile_markdown_to_json(md_file)
    assert json_out.exists()
    assert json_out.name == "flow.json"

    data = json.loads(json_out.read_text(encoding="utf-8"))
    assert data["name"] == "CLI Test"
    assert data["steps"][0]["action"] == "logic.delay"
    assert data["steps"][0]["parameters"]["seconds"] == 1

    # Export back to Markdown
    exported_md = tmp_path / "flow_exported.md"
    export_json_to_markdown(json_out, output_md_path=exported_md)
    assert exported_md.exists()

    # Re-read and check
    re_flow = load_flow(exported_md)
    assert re_flow.name == "CLI Test"
    assert re_flow.steps[0].action == "logic.delay"


def test_condition_backtick_stripping():
    md = """# Condition Test
> Description: Testing condition with backticks
> Version: 1.0.0

## Steps

### 1. Conditional Action (`logic.delay`)
- **condition:** `${has_cookie_banner} == true`
- **seconds:** 1
"""
    flow = markdown_to_flow(md)
    assert flow.steps[0].condition == "${has_cookie_banner} == true"
    
    from kinenix.engine.interpreter import FlowInterpreter
    fi = FlowInterpreter()
    assert fi._evaluate_condition_expr("`true == true`") is True
    assert fi._evaluate_condition_expr("`false == true`") is False



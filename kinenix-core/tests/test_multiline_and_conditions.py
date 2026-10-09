"""Issues #61 (multi-line values) and #48 (conditions split before variables are replaced, `in`, `is empty`)."""
import pytest

from kinenix.engine.conditions import split_condition
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import flow_to_markdown, markdown_issues, markdown_to_flow


def run_flow(markdown, flow_dir):
    return FlowInterpreter().run_flow(markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(flow_dir)})


# --- #61 multi-line values ---------------------------------------------------------------------------

EMAIL = """# Mail

## Steps

### 1. Write Body (`file.write_text`)
- **path:** out.txt
- **content:** |
    สวัสดีครับ

    - แผน: ${plan}
      (ราคาต่อปี)
    จบ
- **append:** false

### 2. Loop (`logic.loop`)
- **items:** ["A"]
- **item_var:** `x`
- **Sub-steps:**
  - Write Nested (`file.write_text`):
    - **path:** nested.txt
    - **content:** |
        line 1

        line 2 ${x}
    - **append:** true
"""


def test_block_value_keeps_lines_blank_lines_and_relative_indent(tmp_path):
    flow = markdown_to_flow(EMAIL)
    assert flow.steps[0].parameters["content"] == "สวัสดีครับ\n\n- แผน: ${plan}\n  (ราคาต่อปี)\nจบ"
    assert flow.steps[0].parameters["append"] is False
    nested = flow.steps[1].sub_steps[0].parameters
    assert nested["content"] == "line 1\n\nline 2 ${x}" and nested["append"] is True
    assert markdown_issues(EMAIL) == []


def test_block_value_runs_with_variables(tmp_path):
    flow = markdown_to_flow(EMAIL)
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(tmp_path), "plan": "ชั้น 1"})
    assert not ctx.has_error
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "สวัสดีครับ\n\n- แผน: ชั้น 1\n  (ราคาต่อปี)\nจบ"
    assert (tmp_path / "nested.txt").read_text(encoding="utf-8") == "line 1\n\nline 2 A\n"


def test_export_writes_blocks_and_round_trips():
    flow = markdown_to_flow(EMAIL)
    exported = flow_to_markdown(flow)
    assert "- **content:** |\n    สวัสดีครับ\n\n    - แผน: ${plan}" in exported
    assert markdown_to_flow(exported).model_dump() == flow.model_dump()


def test_lone_pipe_is_a_value_and_tabs_indent_like_spaces():
    flow = markdown_to_flow("# P\n\n## Steps\n\n### 1. Read (`csv.read`)\n- **file_path:** a.csv\n- **delimiter:** |\n"
                            "\n### 2. Body (`file.write_text`)\n- **path:** b.txt\n- **content:** |\n\tfirst\n\tsecond\n")
    assert flow.steps[0].parameters["delimiter"] == "|"
    assert flow.steps[1].parameters["content"] == "first\nsecond"


def test_lines_without_a_block_are_reported_not_silently_dropped():
    markdown = """# Old Style

## Steps

### 1. Write Body (`file.write_text`)
- **path:** out.txt
- **content:** Hello,
The automated workflow has completed successfully.
"""
    flow = markdown_to_flow(markdown)
    assert flow.steps[0].parameters["content"] == "Hello,"
    issues = markdown_issues(markdown)
    assert len(issues) == 1
    assert "Line 8" in issues[0] and "Write Body" in issues[0] and "|" in issues[0]


# --- #48 conditions ----------------------------------------------------------------------------------

@pytest.mark.parametrize("expression, expected", [
    ("${mileage} contains 5,000", ("${mileage}", "contains", "5,000")),
    ("${row.Role in Company} == 'Programmer'", ("${row.Role in Company}", "equals", "'Programmer'")),
    ("${a} >= 3", ("${a}", "greater_than_or_equal", "3")),
    ("${a} == 'x > y'", ("${a}", "equals", "'x > y'")),
    ("${word} not in ${list}", ("${word}", "not_in", "${list}")),
    ("${name} starts with Mr", ("${name}", "starts_with", "Mr")),
    ("${note} is empty", ("${note}", "is_empty", None)),
    ("${note} is not empty", ("${note}", "is_not_empty", None)),
    ("${flag}", None),
])
def test_split_ignores_operators_inside_placeholders_and_quotes(expression, expected):
    parts = split_condition(expression)
    assert (None if parts is None else tuple(p.strip() if p else p for p in parts)) == expected


CONDITIONS = """# Conditions

## Variables
- `mileage`: < 5,000 km
- `word`: cat
- `note`: ""
- `allowed`: ["HONDA", "TOYOTA"]
- `brand`: honda
- `row`: {"Role in Company": "Programmer"}

## Steps

### 1. Value With Angle Bracket (`logic.set_variable`)
- **condition:** `${mileage} contains 5,000`
- **name:** r1
- **value:** ran

### 2. In Means Left Is Part Of Right (`logic.set_variable`)
- **condition:** `${word} in concatenate`
- **name:** r2
- **value:** ran

### 3. Not In (`logic.set_variable`)
- **condition:** `${word} not in dog`
- **name:** r3
- **value:** ran

### 4. Is Empty (`logic.set_variable`)
- **condition:** `${note} is empty`
- **name:** r4
- **value:** ran

### 5. In A List (`logic.set_variable`)
- **condition:** `${brand} in ${allowed}`
- **name:** r5
- **value:** ran

### 6. Column Name With In (`logic.set_variable`)
- **condition:** `${row.Role in Company} == 'Programmer'`
- **name:** r6
- **value:** ran

### 7. Is Not Empty Is False (`logic.set_variable`)
- **condition:** `${note} is not empty`
- **name:** r7
- **value:** ran

### 8. Ends With (`logic.set_variable`)
- **condition:** `${mileage} ends with km`
- **name:** r8
- **value:** ran
"""


def test_conditions_on_real_values(tmp_path):
    ctx = run_flow(CONDITIONS, tmp_path)
    assert not ctx.has_error
    ran = {f"r{i}": ctx.get_variable(f"r{i}") for i in range(1, 9)}
    assert ran == {"r1": "ran", "r2": "ran", "r3": "ran", "r4": "ran", "r5": "ran", "r6": "ran", "r7": None, "r8": "ran"}


def test_logic_if_uses_the_same_conditions_with_else(tmp_path):
    ctx = run_flow("""# If

## Variables
- `note`: hello

## Steps

### 1. Branch (`logic.if`)
- **condition:** `${note} is empty`
- **Sub-steps:**
  - Then (`logic.set_variable`):
    - **name:** branch
    - **value:** then
- **Else-steps:**
  - Else (`logic.set_variable`):
    - **name:** branch
    - **value:** else
""", tmp_path)
    assert ctx.get_variable("branch") == "else"


def test_operator_in_left_right_form_means_left_in_right(tmp_path):
    ctx = run_flow("""# Left Right

## Steps

### 1. Branch (`logic.if`)
- **left:** cat
- **operator:** in
- **right:** concatenate
- **Sub-steps:**
  - Then (`logic.set_variable`):
    - **name:** branch
    - **value:** then
""", tmp_path)
    assert ctx.get_variable("branch") == "then"

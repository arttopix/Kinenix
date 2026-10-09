"""Issues #46, #47, #53, #59: problems that made a flow do the wrong thing without any warning."""
import csv

import pandas as pd
import pytest

from kinenix.actions.registry import ActionRegistry
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import markdown_to_flow
from kinenix.models.context import ExecutionContext


def run(action, flow_dir, **parameters):
    ctx = ExecutionContext(flow_name="t")
    ctx.set_variable("__flow_dir__", str(flow_dir))
    return ActionRegistry.get(action)().execute(parameters, ctx)


def run_flow(markdown, flow_dir):
    return FlowInterpreter().run_flow(markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(flow_dir)})


# --- #47 csv.read and excel.read: blanks, numbers, codes -------------------------------------------

def test_csv_blanks_are_none_and_whole_numbers_stay_int(tmp_path):
    (tmp_path / "data.csv").write_text("id,name,note,year\nA,Alice,,2023\nB,Bob,hi,\n", encoding="utf-8")
    rows = run("csv.read", tmp_path, file_path="data.csv")
    assert rows == [
        {"id": "A", "name": "Alice", "note": None, "year": 2023},
        {"id": "B", "name": "Bob", "note": "hi", "year": None},
    ]
    assert type(rows[0]["year"]) is int


def test_csv_keeps_codes_text_and_types_numbers(tmp_path):
    (tmp_path / "data.csv").write_text(
        "phone,zip,price,ok,country,mixed\n0812345678,10110,15434.75,TRUE,NA,1\n0899999999,00100,2,false,TH,x\n",
        encoding="utf-8")
    rows = run("csv.read", tmp_path, file_path="data.csv")
    assert rows[0] == {"phone": "0812345678", "zip": "10110", "price": 15434.75, "ok": True, "country": "NA", "mixed": "1"}
    assert rows[1] == {"phone": "0899999999", "zip": "00100", "price": 2.0, "ok": False, "country": "TH", "mixed": "x"}


def test_csv_as_text_keeps_everything_as_written(tmp_path):
    (tmp_path / "data.csv").write_text("year,note\n2023,\n2024,hi\n", encoding="utf-8")
    assert run("csv.read", tmp_path, file_path="data.csv", as_text=True) == [
        {"year": "2023", "note": ""}, {"year": "2024", "note": "hi"}]


def test_csv_from_excel_with_bom_has_clean_headers_and_thai(tmp_path):
    (tmp_path / "excel.csv").write_bytes("ยี่ห้อ,ปี\nHONDA,2023\n".encode("utf-8-sig"))
    assert run("csv.read", tmp_path, file_path="excel.csv") == [{"ยี่ห้อ": "HONDA", "ปี": 2023}]


def test_csv_wrong_encoding_says_how_to_fix(tmp_path):
    (tmp_path / "legacy.csv").write_bytes("ชื่อ\nสมชาย\n".encode("cp874"))
    with pytest.raises(ValueError, match="cp874"):
        run("csv.read", tmp_path, file_path="legacy.csv")
    assert run("csv.read", tmp_path, file_path="legacy.csv", encoding="cp874") == [{"ชื่อ": "สมชาย"}]


def test_blank_cell_never_reaches_a_flow_as_nan(tmp_path):
    (tmp_path / "data.csv").write_text("id,note\nA,\n", encoding="utf-8")
    ctx = run_flow("""# Blank Check

## Steps

### 1. Read (`csv.read`)
- **file_path:** data.csv
- **output_var:** `rows`

### 2. Note Text (`logic.set_variable`)
- **name:** typed
- **value:** [${rows}]
""", tmp_path)
    assert "nan" not in str(ctx.get_variable("typed")).lower()


def test_excel_blanks_are_none_and_whole_numbers_stay_int(tmp_path):
    pd.DataFrame({"name": ["Alice", "Bob"], "year": [2023, None], "note": [None, "hi"]}).to_excel(
        tmp_path / "data.xlsx", index=False)
    rows = run("excel.read", tmp_path, file_path="data.xlsx")
    assert rows == [{"name": "Alice", "year": 2023, "note": None}, {"name": "Bob", "year": None, "note": "hi"}]
    assert type(rows[0]["year"]) is int
    assert run("excel.read", tmp_path, file_path="data.xlsx", as_text=True)[1] == {"name": "Bob", "year": "", "note": "hi"}


# --- #59 csv.write: Excel-friendly encoding and append ----------------------------------------------

def test_csv_write_defaults_to_excel_friendly_bom(tmp_path):
    run("csv.write", tmp_path, file_path="out.csv", data=[{"แผน": "ชั้น 1", "ราคา": 15900}])
    raw = (tmp_path / "out.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert run("csv.read", tmp_path, file_path="out.csv") == [{"แผน": "ชั้น 1", "ราคา": 15900}]

    run("csv.write", tmp_path, file_path="plain.csv", data=[{"a": 1}], encoding="utf-8")
    assert not (tmp_path / "plain.csv").read_bytes().startswith(b"\xef\xbb\xbf")


def test_csv_write_append_writes_header_once_and_follows_it(tmp_path):
    run("csv.write", tmp_path, file_path="log.csv", data=[{"id": "R1", "status": "ok"}], append=True)
    result = run("csv.write", tmp_path, file_path="log.csv", data=[{"status": "failed", "id": "R2"}], append="true")
    assert result["mode"] == "append"
    raw = (tmp_path / "log.csv").read_bytes()
    assert raw.count(b"\xef\xbb\xbf") == 1
    with open(tmp_path / "log.csv", encoding="utf-8-sig", newline="") as handle:
        assert list(csv.reader(handle)) == [["id", "status"], ["R1", "ok"], ["R2", "failed"]]


def test_csv_write_append_refuses_unknown_columns(tmp_path):
    run("csv.write", tmp_path, file_path="log.csv", data=[{"id": "R1"}])
    with pytest.raises(ValueError, match="price"):
        run("csv.write", tmp_path, file_path="log.csv", data=[{"id": "R2", "price": 5}], append=True)


# --- #46 logic.if with condition runs Else-steps ----------------------------------------------------

IF_ELSE = """# If Else

## Variables
- `status`: {status}

## Steps

### 1. Branch On Status (`logic.if`)
- **condition:** `${{status}} == ok`
- **Sub-steps:**
  - Then Branch (`logic.set_variable`):
    - **name:** branch
    - **value:** then
- **Else-steps:**
  - Else Branch (`logic.set_variable`):
    - **name:** branch
    - **value:** else
"""


@pytest.mark.parametrize("status, branch", [("ok", "then"), ("failed", "else")])
def test_logic_if_condition_chooses_the_branch(tmp_path, status, branch):
    ctx = run_flow(IF_ELSE.format(status=status), tmp_path)
    assert not ctx.has_error
    assert ctx.get_variable("branch") == branch
    assert [r.status for r in ctx.step_results if r.step_id == "step_1"] == ["success"]


def test_condition_still_gates_other_actions(tmp_path):
    ctx = run_flow("""# Gate

## Variables
- `status`: failed

## Steps

### 1. Only When Ok (`logic.set_variable`)
- **condition:** `${status} == ok`
- **name:** ran
- **value:** yes
""", tmp_path)
    assert ctx.get_variable("ran") is None


# --- #53 business errors inside a subflow stay business -----------------------------------------------

def test_business_error_in_subflow_is_business_and_not_retried(tmp_path):
    child = markdown_to_flow("""# Child

## Steps

### 1. Count Attempt (`file.write_text`)
- **path:** ${attempts_file}
- **content:** attempt
- **append:** true

### 2. Stop (`flow.fail`)
- **message:** No packages for this car
- **category:** business
""")
    (tmp_path / "subflows").mkdir()
    (tmp_path / "subflows" / "child.json").write_text(child.model_dump_json(), encoding="utf-8")

    ctx = run_flow("""# Parent

## Steps

### 1. Call Child (`flow.call`)
- **flow:** ./subflows/child.json
- **inputs:** {"attempts_file": "${__flow_dir__}/attempts.txt"}
- **on_error:** retry
- **max_retries:** 3
- **retry_interval:** 0
""", tmp_path)
    assert ctx.has_error
    assert ctx.failure_details.error_type == "Business"
    # The subflow ran once: a business error is never retried, even with on_error: retry
    assert (tmp_path / "attempts.txt").read_text(encoding="utf-8") == "attempt\n"

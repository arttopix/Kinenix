"""date.calc: dates relative to today, so a scheduled flow works on the right period each run."""
from datetime import datetime

import pytest

from kinenix.actions import date_time
from kinenix.actions.registry import ActionRegistry
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import markdown_to_flow
from kinenix.models.context import ExecutionContext


@pytest.fixture
def today(monkeypatch):
    """Pins 'today' and 'now' to 8 October 2026, 14:30."""
    monkeypatch.setattr(date_time, "_now", lambda: datetime(2026, 10, 8, 14, 30, 15, 123))


def calc(**parameters):
    return ActionRegistry.get("date.calc")().execute(parameters, ExecutionContext(flow_name="t"))


def test_today_by_default(today):
    result = calc()
    assert result["date"] == "2026-10-08"
    assert result["text"] == "2026-10-08"
    assert (result["year"], result["month"], result["day"]) == (2026, 10, 8)
    assert result["month_name"] == "October" and result["month_abbr"] == "Oct"
    assert result["weekday"] == "Thursday" and result["weekday_number"] == 4
    assert result["hour"] == 0 and result["days_in_month"] == 31


def test_now_keeps_the_time(today):
    result = calc(date="now", format="%Y%m%d_%H%M")
    assert result["text"] == "20261008_1430"
    assert result["datetime"] == "2026-10-08T14:30:15"


def test_previous_month_start_and_end(today):
    assert calc(add_months=-1, snap="start_of_month")["date"] == "2026-09-01"
    end = calc(add_months=-1, snap="end_of_month")
    assert end["date"] == "2026-09-30" and end["day"] == 30 and end["month_name"] == "September"


def test_month_arithmetic_clamps_the_day_and_crosses_years():
    assert calc(date="2026-03-31", add_months=-1)["date"] == "2026-02-28"
    assert calc(date="2024-03-31", add_months=-1)["date"] == "2024-02-29"
    assert calc(date="2026-01-15", add_months=-1)["date"] == "2025-12-15"
    assert calc(date="2026-12-15", add_months=1)["date"] == "2027-01-15"
    assert calc(date="2024-02-29", add_years=1)["date"] == "2025-02-28"


def test_days_weeks_and_snaps():
    assert calc(date="2026-10-08", add_days=-8)["date"] == "2026-09-30"
    assert calc(date="2026-10-08", add_weeks=2)["date"] == "2026-10-22"
    assert calc(date="2026-10-08", snap="start_of_week")["date"] == "2026-10-05"
    assert calc(date="2026-10-08", snap="end_of_week")["date"] == "2026-10-11"
    assert calc(date="2026-10-08", snap="start_of_year")["date"] == "2026-01-01"
    assert calc(date="2026-10-08", snap="end_of_year")["date"] == "2026-12-31"


def test_reads_dates_in_other_formats():
    assert calc(date="31/12/2024", input_format="%d/%m/%Y")["date"] == "2024-12-31"
    assert calc(date="2024-12-31T09:15:00", format="%H:%M")["text"] == "09:15"


def test_numbers_from_variables_may_be_strings():
    assert calc(date="2026-10-08", add_days="-1")["date"] == "2026-10-07"


@pytest.mark.parametrize("parameters, message", [
    ({"date": "next tuesday"}, "could not read date"),
    ({"date": "2024-31-12", "input_format": "%d/%m/%Y"}, "input_format"),
    ({"date": "2026-10-08", "snap": "middle_of_month"}, "snap must be one of"),
    ({"date": "2026-10-08", "add_days": "one"}, "whole number"),
])
def test_clear_errors(parameters, message):
    with pytest.raises(ValueError, match=message):
        calc(**parameters)


def test_flow_uses_the_parts_of_a_date(today, tmp_path):
    flow = markdown_to_flow("""# Last Month Report

## Steps

### 1. First Day Of Last Month (`date.calc`)
- **add_months:** -1
- **snap:** start_of_month
- **output_var:** `start`

### 2. Report File Name (`logic.set_variable`)
- **name:** report_path
- **value:** ./output/fx_${start.year}-${start.month_abbr}.csv

### 3. Year As Number (`logic.set_variable`)
- **name:** report_year
- **value:** `${start.year}`
""")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(tmp_path)})
    assert not ctx.has_error
    assert ctx.get_variable("report_path") == "./output/fx_2026-Sep.csv"
    assert ctx.get_variable("report_year") == 2026

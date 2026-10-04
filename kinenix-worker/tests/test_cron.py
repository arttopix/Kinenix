import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from kinenix_worker.triggers.cron import CronExpression
from kinenix_worker.triggers.manager import TriggerManager
from kinenix_worker.triggers.scheduler import CronSchedulerTrigger


@pytest.mark.parametrize("expr, moment, expected", [
    ("0 8 1 * *", datetime(2026, 11, 1, 8, 0), True),
    ("0 8 1 * *", datetime(2026, 11, 1, 8, 1), False),
    ("0 8 1 * *", datetime(2026, 11, 2, 8, 0), False),
    ("*/15 * * * *", datetime(2026, 1, 1, 3, 45), True),
    ("*/15 * * * *", datetime(2026, 1, 1, 3, 46), False),
    ("30 7 * * 1-5", datetime(2026, 10, 5, 7, 30), True),    # Monday
    ("30 7 * * 1-5", datetime(2026, 10, 4, 7, 30), False),   # Sunday
    ("0 0 * * 0", datetime(2026, 10, 4, 0, 0), True),        # Sunday as 0
    ("0 0 * * 7", datetime(2026, 10, 4, 0, 0), True),        # Sunday as 7
    ("0 9 1,15 * *", datetime(2026, 10, 15, 9, 0), True),
    ("5/20 * * * *", datetime(2026, 1, 1, 0, 45), True),
    ("0 12 13 * 5", datetime(2026, 11, 13, 12, 0), True),    # day 13 (a Friday): either field may match
    ("0 12 13 * 5", datetime(2026, 10, 9, 12, 0), True),     # a Friday that is not the 13th
    ("0 12 13 * 5", datetime(2026, 10, 8, 12, 0), False),
])
def test_cron_matches(expr, moment, expected):
    assert CronExpression(expr).matches(moment) is expected


@pytest.mark.parametrize("expr", ["0 8 * *", "60 * * * *", "* 24 * * *", "* * 0 * *", "*/0 * * * *", "a * * * *", "5-1 * * * *"])
def test_cron_rejects_invalid(expr):
    with pytest.raises(ValueError):
        CronExpression(expr)


def test_scheduler_runs_once_per_matching_minute():
    runner = MagicMock()
    runner.execute_flow.return_value = {"status": "success"}
    sched = CronSchedulerTrigger(flow_path="flow.json", runner=runner, cron="0 8 1 * *")
    assert sched.describe() == "cron '0 8 1 * *'"

    assert sched.check_and_run(datetime(2026, 11, 1, 7, 59, 59)) is None
    assert sched.check_and_run(datetime(2026, 11, 1, 8, 0, 1)) == {"status": "success"}
    assert sched.check_and_run(datetime(2026, 11, 1, 8, 0, 30)) is None   # same minute
    assert sched.check_and_run(datetime(2026, 12, 1, 8, 0, 0)) == {"status": "success"}
    assert runner.execute_flow.call_count == 2
    assert runner.execute_flow.call_args.kwargs["extra_vars"]["trigger_timestamp"] == "2026-12-01T08:00:00"


def test_manager_loads_cron_trigger(tmp_path):
    config = tmp_path / "triggers.json"
    config.write_text(json.dumps({"triggers": [
        {"type": "scheduler", "flow": "flows/examples/bot_fx_rate", "cron": "0 8 1 * *"},
        {"type": "scheduler", "flow": "x", "interval_seconds": 30},
    ]}), encoding="utf-8")
    manager = TriggerManager(runner=MagicMock())
    manager.load_from_config(str(config))
    assert str(manager.triggers[0].cron) == "0 8 1 * *"
    assert manager.triggers[1].cron is None and manager.triggers[1].interval_seconds == 30

    config.write_text(json.dumps([{"type": "cron", "flow": "x", "cron": "0 25 * * *"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="hour"):
        TriggerManager(runner=MagicMock()).load_from_config(str(config))

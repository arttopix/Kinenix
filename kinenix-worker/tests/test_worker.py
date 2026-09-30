import json
from pathlib import Path
import pytest

from kinenix_worker.runner import WorkerRunner
from kinenix.models.flow import FlowDefinition, Step


def test_worker_system_info():
    info = WorkerRunner.get_system_info()
    assert "os" in info
    assert "machine" in info
    assert "cpu_count" in info
    assert "memory_total_mb" in info
    assert info["cpu_count"] > 0


def test_worker_execute_simple_flow(tmp_path: Path):
    flow_file = tmp_path / "flow.json"
    flow_content = {
        "name": "Worker Simple Test Flow",
        "variables": {
            "test_key": "initial_value"
        },
        "steps": [
            {
                "id": "step_1",
                "name": "Set Test Variable",
                "action": "logic.set_variable",
                "parameters": {
                    "name": "test_key",
                    "value": "worker_executed_successfully"
                }
            }
        ]
    }
    flow_file.write_text(json.dumps(flow_content), encoding="utf-8")

    runner = WorkerRunner()
    result = runner.execute_flow(str(flow_file), log_dir=str(tmp_path / "logs"))

    assert result["status"] == "success"
    assert result["has_error"] is False
    assert result["steps_executed"] == 1
    assert result["flow_name"] == "Worker Simple Test Flow"
    assert "worker_system" in result

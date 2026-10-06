"""The worker finds a flow by name in the flows folder, so triggers.json can say "flow": "get_stock_data"."""
from unittest.mock import MagicMock

import pytest

from kinenix.scaffold import create_project
from kinenix_worker.hub_client import HubClient
from kinenix_worker.runner import WorkerRunner


def test_flow_name_resolves_in_the_flows_folder(tmp_path, monkeypatch):
    flows = tmp_path / "flows"
    create_project(flows / "greeter", "hello")
    monkeypatch.setenv("KINENIX_FLOWS_DIR", str(flows))
    monkeypatch.chdir(tmp_path)  # not inside the flows folder

    client = MagicMock(spec=HubClient)
    client.worker_id = "w"
    result = WorkerRunner(client=client).execute_flow("greeter", log_dir=str(tmp_path / "logs"))

    assert result["status"] == "success"
    assert (flows / "greeter" / "output" / "greetings.csv").is_file()


def test_unknown_name_still_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.setenv("KINENIX_FLOWS_DIR", str(tmp_path / "flows"))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="no_such_flow"):
        WorkerRunner(client=MagicMock(spec=HubClient, worker_id="w")).execute_flow("no_such_flow")

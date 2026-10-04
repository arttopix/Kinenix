import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.models.context import ExecutionContext
from kinenix.models.flow import FlowDefinition, Step


def _send(monkeypatch, api_key):
    if api_key is None:
        monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    else:
        monkeypatch.setenv("KINENIX_HUB_API_KEY", api_key)

    exec_logger = ExecutionLogger()
    context = ExecutionContext(flow_name="Telemetry Auth Test")
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        exec_logger._send_telemetry("http://hub:8080/", {"flow_name": "X"}, context)
    return mock_post


def test_telemetry_sends_api_key_header_when_configured(monkeypatch):
    mock_post = _send(monkeypatch, "s3cret-key")
    args, kwargs = mock_post.call_args
    assert args[0] == "http://hub:8080/api/v1/telemetry"
    assert kwargs["headers"] == {"X-API-Key": "s3cret-key"}


def test_telemetry_omits_api_key_header_when_not_configured(monkeypatch):
    mock_post = _send(monkeypatch, None)
    assert "X-API-Key" not in mock_post.call_args.kwargs["headers"]


def test_telemetry_payload_with_datetimes_is_sent(monkeypatch):
    monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    exec_logger = ExecutionLogger()
    context = ExecutionContext(flow_name="Datetime Payload Test")
    raw_data = context.model_dump(mode="python")
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        exec_logger._send_telemetry("http://hub:8080", raw_data, context)
    assert mock_post.called
    body = mock_post.call_args.kwargs["json"]
    json.dumps(body)  # raises TypeError if any datetime slipped through
    assert isinstance(body["payload"]["start_time"], str)


def test_telemetry_timestamps_carry_utc_offset(monkeypatch):
    # The Hub converts timestamps to UTC, which requires an explicit offset
    monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    flow = FlowDefinition(
        name="Timezone Test",
        steps=[Step(id="s1", name="Set", action="logic.set_variable", parameters={"name": "x", "value": "1"})],
    )
    context = FlowInterpreter().run_flow(flow)

    assert context.start_time.utcoffset() is not None
    assert context.step_results[0].start_time.utcoffset() is not None
    assert context.step_results[0].end_time.utcoffset() is not None

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        ExecutionLogger()._send_telemetry("http://hub:8080", context.model_dump(mode="python"), context)
    sent = datetime.fromisoformat(mock_post.call_args.kwargs["json"]["payload"]["start_time"])
    assert sent.utcoffset() is not None
    assert sent == context.start_time


def test_telemetry_is_sent_without_a_log_dir(monkeypatch):
    # Workers run without --log-dir; telemetry must still reach the Hub
    monkeypatch.setenv("KINENIX_HUB_URL", "http://hub:8080")
    monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    flow = FlowDefinition(
        name="No Log Dir",
        steps=[Step(id="s1", name="Set", action="logic.set_variable", parameters={"name": "x", "value": "1"})],
    )
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        FlowInterpreter(logger=ExecutionLogger(log_dir=None)).run_flow(flow)
    assert mock_post.called
    assert mock_post.call_args.args[0] == "http://hub:8080/api/v1/telemetry"

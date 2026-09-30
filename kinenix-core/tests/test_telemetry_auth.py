import json
from unittest.mock import MagicMock, patch

from kinenix.engine.logger import ExecutionLogger
from kinenix.models.context import ExecutionContext


def _send(monkeypatch, api_key):
    if api_key is None:
        monkeypatch.delenv("KINENIX_ORCHESTRATOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("KINENIX_ORCHESTRATOR_API_KEY", api_key)

    exec_logger = ExecutionLogger()
    context = ExecutionContext(flow_name="Telemetry Auth Test")
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        exec_logger._send_telemetry("http://orchestrator:8080/", {"flow_name": "X"}, context)
    return mock_post


def test_telemetry_sends_api_key_header_when_configured(monkeypatch):
    mock_post = _send(monkeypatch, "s3cret-key")
    args, kwargs = mock_post.call_args
    assert args[0] == "http://orchestrator:8080/api/v1/telemetry"
    assert kwargs["headers"] == {"X-API-Key": "s3cret-key"}


def test_telemetry_omits_api_key_header_when_not_configured(monkeypatch):
    mock_post = _send(monkeypatch, None)
    assert "X-API-Key" not in mock_post.call_args.kwargs["headers"]


def test_telemetry_payload_with_datetimes_is_sent(monkeypatch):
    monkeypatch.delenv("KINENIX_ORCHESTRATOR_API_KEY", raising=False)
    exec_logger = ExecutionLogger()
    context = ExecutionContext(flow_name="Datetime Payload Test")
    raw_data = context.model_dump(mode="python")
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        exec_logger._send_telemetry("http://orchestrator:8080", raw_data, context)
    assert mock_post.called
    body = mock_post.call_args.kwargs["json"]
    json.dumps(body)  # raises TypeError if any datetime slipped through
    assert isinstance(body["payload"]["start_time"], str)

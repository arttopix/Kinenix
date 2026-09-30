from unittest.mock import MagicMock, patch
import pytest

from kinenix.actions.registry import ActionRegistry
from kinenix.models.context import ExecutionContext
from kinenix.models.flow import FlowDefinition, Step
from kinenix.engine.interpreter import FlowInterpreter


def test_ai_prompt_action_registered():
    action_cls = ActionRegistry.get("ai.prompt")
    assert action_cls is not None


def test_ai_extract_action_registered():
    action_cls = ActionRegistry.get("ai.extract")
    assert action_cls is not None


def test_http_download_action_registered():
    action_cls = ActionRegistry.get("http.download")
    assert action_cls is not None


def test_csv_write_action_registered():
    action_cls = ActionRegistry.get("csv.write")
    assert action_cls is not None


@patch("requests.post")
def test_ai_prompt_execution_with_json_parsing(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": '{"InvoiceNo": "10021", "TotalDue": 1234.40}',
        "total_duration": 500000000
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    ctx = ExecutionContext(flow_name="TestFlow")
    action_cls = ActionRegistry.get("ai.prompt")
    action = action_cls()

    res = action.execute(
        {
            "prompt": "Extract invoice fields",
            "format": "json",
            "model": "qwen2.5:1.5b"
        },
        ctx
    )

    assert isinstance(res["response"], dict)
    assert res["response"]["InvoiceNo"] == "10021"
    assert res["response"]["TotalDue"] == 1234.40
    assert res["model"] == "qwen2.5:1.5b"


@patch("requests.post")
def test_ai_extract_execution(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": '```json\n{"InvoiceNo": "INV-999", "CompanyName": "Acme Corp"}\n```',
        "total_duration": 400000000
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    ctx = ExecutionContext(flow_name="TestFlow")
    action_cls = ActionRegistry.get("ai.extract")
    action = action_cls()

    extracted = action.execute(
        {
            "instructions": "Extract invoice details",
            "schema": ["InvoiceNo", "CompanyName"],
            "text": "Invoice: INV-999 from Acme Corp",
            "model": "qwen2.5:1.5b"
        },
        ctx
    )

    assert isinstance(extracted, dict)
    assert extracted["InvoiceNo"] == "INV-999"
    assert extracted["CompanyName"] == "Acme Corp"


@patch("requests.post")
def test_flow_interpreter_with_ai_action(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": '{"InvoiceNo": "10021", "TotalDue": "1234.40", "CompanyName": "Sit Amet Corp."}'
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    flow = FlowDefinition(
        name="AI Test Flow",
        steps=[
            Step(
                id="extract_step",
                name="Extract Invoice Info",
                action="ai.extract",
                parameters={
                    "text": "Sample text invoice",
                    "schema": ["InvoiceNo", "TotalDue", "CompanyName"]
                },
                output_var="invoice_data"
            )
        ]
    )

    interpreter = FlowInterpreter()
    ctx = interpreter.run_flow(flow)

    assert ctx.is_completed is True
    assert ctx.has_error is False
    data = ctx.get_variable("invoice_data")
    assert data["InvoiceNo"] == "10021"
    assert data["CompanyName"] == "Sit Amet Corp."

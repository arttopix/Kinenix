import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from kinenix.actions.registry import ActionRegistry
from kinenix.models.context import ExecutionContext


def test_ai_decide_registered():
    """Verify ai.decide action is properly registered in ActionRegistry."""
    action_cls = ActionRegistry.get("ai.decide")
    assert action_cls is not None
    assert action_cls.action_type == "ai.decide"


def test_ai_decide_choice_single_question():
    """Verify ai.decide unwraps single-question answers cleanly."""
    action_cls = ActionRegistry.get("ai.decide")
    action = action_cls()
    ctx = ExecutionContext(flow_name="TestSystemOne")

    mock_resp_data = {
        "model": "openthai-systemone",
        "answers": {
            "department": {
                "type": "choice",
                "choice": "ฝ่ายการเงิน",
                "probabilities": {"ฝ่ายการเงิน": 0.95, "ฝ่ายบุคคล": 0.05},
                "confidence": 0.90
            }
        },
        "usage": {"input_tokens": 50, "output_tokens": 0}
    }

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_resp_data
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        res = action.execute(
            {
                "state": "ขอใบเสร็จรับเงินสำหรับงวดที่แล้ว",
                "question": {
                    "name": "department",
                    "type": "choice",
                    "instructions": "แผนกใดควรดูแลเคสนี้",
                    "options": ["ฝ่ายการเงิน", "ฝ่ายบุคคล"]
                }
            },
            ctx
        )

        assert res["choice"] == "ฝ่ายการเงิน"
        assert res["confidence"] == 0.90
        assert res["type"] == "choice"
        assert res["model"] == "openthai-systemone"

        # Verify sent payload converted options list to criteria dict
        called_payload = mock_post.call_args[1]["json"]
        assert called_payload["state"] == "ขอใบเสร็จรับเงินสำหรับงวดที่แล้ว"
        criteria = called_payload["questions"]["department"]["criteria"]
        assert "ฝ่ายการเงิน" in criteria
        assert "ฝ่ายบุคคล" in criteria


def test_ai_decide_multiple_questions():
    """Verify ai.decide returns the full answers dict for multiple questions."""
    action_cls = ActionRegistry.get("ai.decide")
    action = action_cls()
    ctx = ExecutionContext(flow_name="TestSystemOneMulti")

    mock_resp_data = {
        "model": "openthai-systemone",
        "answers": {
            "intent": {
                "type": "choice",
                "choice": "ร้องเรียน",
                "confidence": 0.88
            },
            "urgency": {
                "type": "score",
                "score": 5,
                "confidence": 0.92
            }
        },
        "usage": {"input_tokens": 100, "output_tokens": 0}
    }

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_resp_data
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        res = action.execute(
            {
                "state": "ระบบล่มตั้งแต่เช้า ลูกค้าโวยวายหนักมาก ด่วนที่สุด",
                "questions": {
                    "intent": {
                        "type": "choice",
                        "options": ["สอบถาม", "ร้องเรียน"]
                    },
                    "urgency": {
                        "type": "score",
                        "instructions": "ประเมินความเร่งด่วน 1-5"
                    }
                }
            },
            ctx
        )

        assert "answers" in res
        assert res["answers"]["intent"]["choice"] == "ร้องเรียน"
        assert res["answers"]["urgency"]["score"] == 5


def test_ai_decide_fallback_to_ollama_on_connection_error():
    """Verify ai.decide falls back to Ollama if SystemOne server is unreachable."""
    action_cls = ActionRegistry.get("ai.decide")
    action = action_cls()
    ctx = ExecutionContext(flow_name="TestFallback")

    def mock_requests_post(url, **kwargs):
        if "8000" in url:
            raise requests.exceptions.ConnectionError("SystemOne offline")
        elif "11434" in url:
            mock_ollama_resp = MagicMock()
            mock_ollama_resp.json.return_value = {
                "response": json.dumps({"choice": "HR"})
            }
            mock_ollama_resp.raise_for_status = MagicMock()
            return mock_ollama_resp
        raise RuntimeError("Unexpected URL")

    with patch("requests.post", side_effect=mock_requests_post):
        res = action.execute(
            {
                "state": "ลาป่วย 1 วัน",
                "question": {
                    "name": "topic",
                    "type": "choice",
                    "options": ["HR", "IT"]
                },
                "fallback_to_ollama": True
            },
            ctx
        )

        assert res["choice"] == "HR"
        assert res["model"] == "ollama-fallback"


def test_web_select_option_ai_match_fast_path():
    """Verify that when an exact match exists in the dropdown, AI call is skipped (fast-path)."""
    action_cls = ActionRegistry.get("web.select_option")
    action = action_cls()
    ctx = ExecutionContext(flow_name="TestWebSelect")

    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first

    # Simulate DOM <option> list
    mock_first.evaluate.return_value = [
        {"text": "กรุงเทพมหานคร", "value": "BKK"},
        {"text": "เชียงใหม่", "value": "CNX"}
    ]
    mock_first.select_option.return_value = ["BKK"]

    mock_page = MagicMock()
    mock_page.locator.return_value = mock_locator
    ctx.set_variable("__playwright_page__", mock_page)

    with patch("requests.post") as mock_post:
        res = action.execute(
            {
                "selector": "#province",
                "text": "กรุงเทพมหานคร",
                "ai_match": True
            },
            ctx
        )

        # Exact match should NOT call SystemOne API
        mock_post.assert_not_called()
        assert res["status"] == "selected"
        assert res["match_type"] == "exact"
        assert res["matched_text"] == "กรุงเทพมหานคร"
        mock_first.select_option.assert_called_once_with(value="BKK")


def test_web_select_option_ai_match_semantic():
    """Verify that an abbreviation like 'กทม.' calls SystemOne and selects 'กรุงเทพมหานคร'."""
    action_cls = ActionRegistry.get("web.select_option")
    action = action_cls()
    ctx = ExecutionContext(flow_name="TestWebSelectSemantic")

    mock_locator = MagicMock()
    mock_first = MagicMock()
    mock_locator.first = mock_first

    mock_first.evaluate.return_value = [
        {"text": "กระบี่", "value": "KB"},
        {"text": "กรุงเทพมหานคร", "value": "BKK"},
        {"text": "กาญจนบุรี", "value": "KAN"}
    ]
    mock_first.select_option.return_value = ["BKK"]

    mock_page = MagicMock()
    mock_page.locator.return_value = mock_locator
    ctx.set_variable("__playwright_page__", mock_page)

    mock_systemone_response = {
        "model": "openthai-systemone",
        "answers": {
            "selected_option": {
                "type": "choice",
                "choice": "กรุงเทพมหานคร",
                "confidence": 0.93
            }
        },
        "usage": {"input_tokens": 40, "output_tokens": 0}
    }

    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_systemone_response
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        res = action.execute(
            {
                "selector": "#province",
                "text": "กทม.",
                "ai_match": True
            },
            ctx
        )

        mock_post.assert_called_once()
        assert res["status"] == "selected"
        assert res["match_type"] == "semantic"
        assert res["matched_text"] == "กรุงเทพมหานคร"
        assert res["confidence"] == 0.93
        mock_first.select_option.assert_called_once_with(value="BKK")


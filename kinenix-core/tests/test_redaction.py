"""Phase 2 guardrail 1: secrets and personal data are removed from logs and Hub telemetry on the worker."""
import json
import logging
import os
from unittest.mock import MagicMock, patch

from kinenix.actions import web_playwright
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.redaction import Redactor, is_thai_id, passes_luhn
from kinenix.models.context import ExecutionContext

THAI_ID = "1101700230708"   # valid check digit
CARD = "4111 1111 1111 1111"  # passes Luhn


def test_values_under_secret_keys_are_hidden_everywhere():
    data = {"config": {"smtp_password": "hunter22", "url": "https://example.com", "use_token": True},
            "error": "Login as admin with hunter22 failed"}
    out = Redactor().redact(data)
    assert out["config"]["smtp_password"] == "****"
    assert out["config"]["url"] == "https://example.com"
    assert out["config"]["use_token"] is True
    harmless = {"cookie_decision": "accepted", "Access-Control-Allow-Credentials": "true", "cookies": [{"v": "x"}]}
    assert Redactor().redact(harmless) == {**harmless, "cookies": "****"}
    assert out["error"] == "Login as admin with **** failed"
    assert data["config"]["smtp_password"] == "hunter22"  # the original is not changed


def test_secret_pairs_in_text_are_hidden():
    r = Redactor()
    assert r.redact("GET https://x.test/api?token=abc123&page=2") == "GET https://x.test/api?token=****&page=2"
    assert r.redact("Authorization: Bearer eyJabc.def") == "Authorization: ****"


def test_thai_id_and_card_numbers_are_replaced_only_when_their_check_passes():
    assert is_thai_id(THAI_ID) and not is_thai_id("1101700230706")
    assert passes_luhn("4111111111111111") and not passes_luhn("4111111111111112")
    r = Redactor()
    assert r.redact(f"ID {THAI_ID}, card {CARD}") == "ID [thai-id], card [card]"
    assert r.redact("1-1017-00230-70-8") == "[thai-id]"
    assert r.redact("order 1101700230706") == "order 1101700230706"
    assert r.redact({"id": int(THAI_ID), "count": 12}) == {"id": "[thai-id]", "count": 12}
    assert r.redact("took 0.1234567890123456 s") == "took 0.1234567890123456 s"


def test_contacts_are_hidden_unless_turned_off():
    text = "Call 081-234-5678 or 02 123 4567, mail somchai@example.co.th"
    r = Redactor()
    assert r.redact(text) == "Call [phone] or [phone], mail [email]"
    r.configure({"redact_contacts": False})
    assert r.redact(text) == text
    assert Redactor().redact("2026-10-13 run 12345") == "2026-10-13 run 12345"


def test_fields_listed_in_config_redact_are_hidden():
    r = Redactor()
    r.configure({"redact": ["customer_name", "Policy_No"]})
    rows = [{"customer_name": "Somchai Jaidee", "policy_no": "P-77881", "premium": 1200}]
    out = r.redact({"rows": rows, "message": "Somchai Jaidee has no quote"})
    assert out["rows"] == [{"customer_name": "****", "policy_no": "****", "premium": 1200}]
    assert out["message"] == "**** has no quote"


def _log_file(log_dir):
    files = list(log_dir.rglob("*.json"))
    assert len(files) == 1
    return files[0].read_text(encoding="utf-8")


def test_env_secrets_are_kept_in_the_run_but_not_in_the_log_or_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("KINENIX_HUB_URL", "http://hub:8080")
    monkeypatch.delenv("KINENIX_HUB_API_KEY", raising=False)
    monkeypatch.setenv("KX_TEST_SITE_LOGIN", "s3cr3t-value")
    bundle = tmp_path / "bundle"
    (bundle / "config").mkdir(parents=True)
    (bundle / "config" / "config.json").write_text(json.dumps({"smtp_password": "cfg-pass-9"}), encoding="utf-8")
    (bundle / ".env").write_text("KX_TEST_DOTENV_VALUE=from-dotenv-42\n", encoding="utf-8")
    flow = markdown_to_flow("""# Secrets

## Steps

### 1. Login (`logic.set_variable`)
- **name:** login
- **value:** ${env.KX_TEST_SITE_LOGIN}|${env.KX_TEST_DOTENV_VALUE}
""")
    try:
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
                flow, initial_vars={"__flow_dir__": str(bundle)})
    finally:
        os.environ.pop("KX_TEST_DOTENV_VALUE", None)

    assert not ctx.has_error, ctx.failure_details
    assert ctx.variables["login"] == "s3cr3t-value|from-dotenv-42"
    assert "__redactor__" not in ctx.variables
    sent = json.dumps(mock_post.call_args.kwargs["json"])
    written = _log_file(tmp_path / "logs")
    for text in (sent, written):
        for secret in ("s3cr3t-value", "from-dotenv-42", "cfg-pass-9"):
            assert secret not in text
        assert "****|****" in text


def test_error_messages_are_redacted_on_the_console_and_in_failure_details(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("KINENIX_HUB_URL", raising=False)
    monkeypatch.setenv("KX_TEST_FOLDER_TOKEN", "folder-key-77")
    flow = markdown_to_flow("""# Failing

## Steps

### 1. Read (`file.read_text`)
- **path:** ./missing/${env.KX_TEST_FOLDER_TOKEN}.txt
""")
    with caplog.at_level(logging.INFO, logger="kinenix"):
        ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
            flow, initial_vars={"__flow_dir__": str(tmp_path)})
    assert ctx.has_error
    assert "folder-key-77" not in caplog.text
    assert "folder-key-77" not in _log_file(tmp_path / "logs")


def test_subflow_secrets_are_hidden_in_the_parent_log(tmp_path, monkeypatch):
    monkeypatch.delenv("KINENIX_HUB_URL", raising=False)
    monkeypatch.setenv("KX_TEST_CHILD_KEY", "child-only-secret")
    bundle = tmp_path / "bundle"
    (bundle / "subflows").mkdir(parents=True)
    (bundle / "subflows" / "child.md").write_text("""# Child

## Steps

### 1. Keep (`flow.return`)
- **value:** ${env.KX_TEST_CHILD_KEY}
""", encoding="utf-8")
    flow = markdown_to_flow("""# Parent

## Steps

### 1. Call (`flow.call`)
- **flow:** ./subflows/child.md
- **output_var:** got
""")
    log_dir = tmp_path / "logs"
    ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=log_dir)).run_flow(
        flow, initial_vars={"__flow_dir__": str(bundle)})
    assert not ctx.has_error, ctx.failure_details
    assert ctx.variables["got"] == "child-only-secret"
    for log in log_dir.rglob("*.json"):
        assert "child-only-secret" not in log.read_text(encoding="utf-8")


class _FakeLocator:
    def __init__(self, input_type):
        self.input_type = input_type
        self.filled = None

    @property
    def first(self):
        return self

    def fill(self, text):
        self.filled = text

    def get_attribute(self, name):
        return self.input_type


def _type(monkeypatch, input_type, **params):
    locator = _FakeLocator(input_type)
    monkeypatch.setattr(web_playwright, "_get_page", lambda context: None)
    monkeypatch.setattr(web_playwright, "_resolve_locator", lambda page, parameters: locator)
    context = ExecutionContext(flow_name="Type")
    redactor = Redactor()
    context.set_variable("__redactor__", redactor)
    output = web_playwright.WebTypeAction().execute({"selector": "#f", "text": "pa55word!", **params}, context)
    return locator, output, redactor


def test_web_type_hides_text_typed_into_a_password_field(monkeypatch):
    locator, output, redactor = _type(monkeypatch, "password")
    assert locator.filled == "pa55word!"
    assert output["text"] == "****"
    assert redactor.redact("echo pa55word!") == "echo ****"


def test_web_type_secret_parameter_and_plain_fields(monkeypatch):
    _, output, _ = _type(monkeypatch, "text", secret=True)
    assert output["text"] == "****"
    _, output, redactor = _type(monkeypatch, "text")
    assert output["text"] == "pa55word!"
    assert redactor.redact("echo pa55word!") == "echo pa55word!"

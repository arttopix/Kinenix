"""email.send against a local fake SMTP server, so the real message can be checked without an email account."""
import base64
import email
import socketserver
import threading

import pytest

from kinenix.actions.registry import ActionRegistry
from kinenix.models.context import ExecutionContext


class _FakeSmtpHandler(socketserver.StreamRequestHandler):
    """Speaks just enough SMTP for smtplib: EHLO with AUTH PLAIN, MAIL, RCPT, DATA, QUIT."""

    def _reply(self, line: str) -> None:
        self.wfile.write((line + "\r\n").encode("ascii"))

    def handle(self):
        server = self.server
        mail = {"from": None, "rcpt": [], "auth": None, "data": None}
        self._reply("220 fake-smtp ready")
        while True:
            raw = self.rfile.readline()
            if not raw:
                return
            line = raw.decode("utf-8").rstrip("\r\n")
            command = line.upper()
            if command.startswith(("EHLO", "HELO")):
                self._reply("250-fake-smtp")
                self._reply("250 AUTH PLAIN")
            elif command.startswith("AUTH PLAIN"):
                _, user, password = base64.b64decode(line.split()[2]).decode("utf-8").split("\0")
                mail["auth"] = (user, password)
                self._reply("235 Authentication successful")
            elif command.startswith("MAIL FROM:"):
                mail["from"] = line[10:].strip("<> ")
                self._reply("250 OK")
            elif command.startswith("RCPT TO:"):
                mail["rcpt"].append(line[8:].strip("<> "))
                self._reply("250 OK")
            elif command == "DATA":
                self._reply("354 End data with <CR><LF>.<CR><LF>")
                lines = []
                while True:
                    data_line = self.rfile.readline().decode("utf-8")
                    if data_line in (".\r\n", ".\n"):
                        break
                    lines.append(data_line[1:] if data_line.startswith("..") else data_line)
                mail["data"] = "".join(lines)
                server.messages.append(dict(mail))
                self._reply("250 Queued")
            elif command == "QUIT":
                self._reply("221 Bye")
                return
            else:
                self._reply("250 OK")


@pytest.fixture
def smtp_server():
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _FakeSmtpHandler)
    server.daemon_threads = True
    server.messages = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def no_smtp_env(monkeypatch):
    for name in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "GMAIL_USER", "GMAIL_APP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)


def _send(params, tmp_path):
    ctx = ExecutionContext(flow_name="Mail")
    ctx.set_variable("__flow_dir__", str(tmp_path))
    return ActionRegistry.get("email.send")().execute(params, ctx)


def test_sends_message_with_attachment_and_all_recipients(smtp_server, no_smtp_env, tmp_path):
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "rates.csv").write_bytes(b"Currency,Rate\nUSD,33.8296\n")
    port = smtp_server.server_address[1]

    res = _send({
        "to": ["a@example.com", "b@example.com"], "cc": "c@example.com", "bcc": ["d@example.com"],
        "subject": "Rates ทดสอบ", "body": "Hello", "html": "<p>Hello</p>",
        "attachments": ["./output/rates.csv"],
        "smtp_host": "127.0.0.1", "smtp_port": port, "use_tls": False,
        "smtp_user": "robot@example.com", "smtp_password": "secret",
    }, tmp_path)

    assert res["status"] == "sent"
    assert res["channel"] == f"SMTP 127.0.0.1:{port}"
    [mail] = smtp_server.messages
    assert mail["auth"] == ("robot@example.com", "secret")
    assert mail["from"] == "robot@example.com"
    assert mail["rcpt"] == ["a@example.com", "b@example.com", "c@example.com", "d@example.com"]

    msg = email.message_from_string(mail["data"])
    assert str(email.header.make_header(email.header.decode_header(msg["Subject"]))) == "Rates ทดสอบ"
    assert msg["Cc"] == "c@example.com" and "d@example.com" not in mail["data"]  # bcc stays hidden
    assert msg.get_content_type() == "multipart/mixed"
    body, attachment = msg.get_payload()
    assert body.get_content_type() == "multipart/alternative"
    assert [p.get_content_type() for p in body.get_payload()] == ["text/plain", "text/html"]
    assert attachment.get_filename() == "rates.csv"
    assert attachment.get_payload(decode=True) == b"Currency,Rate\nUSD,33.8296\n"


def test_environment_pairs_are_not_mixed(smtp_server, no_smtp_env, monkeypatch, tmp_path):
    port = smtp_server.server_address[1]
    monkeypatch.setenv("SMTP_HOST", "127.0.0.1")
    monkeypatch.setenv("SMTP_PORT", str(port))
    monkeypatch.setenv("GMAIL_USER", "me@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "gmail-pass")
    monkeypatch.setenv("SMTP_USER", "me@company.com")
    monkeypatch.setenv("SMTP_PASSWORD", "company-pass")

    _send({"to": "x@example.com", "body": "hi", "use_tls": False}, tmp_path)
    assert smtp_server.messages[-1]["auth"] == ("me@company.com", "company-pass")

    monkeypatch.delenv("SMTP_USER")
    monkeypatch.delenv("SMTP_PASSWORD")
    _send({"to": "x@example.com", "body": "hi", "use_tls": False}, tmp_path)
    assert smtp_server.messages[-1]["auth"] == ("me@gmail.com", "gmail-pass")


def test_dry_run_reports_server_and_checks_attachments(no_smtp_env, tmp_path):
    res = _send({"to": "x@example.com", "dry_run": True, "smtp_host": "smtp.office365.com"}, tmp_path)
    assert res["status"] == "simulated"
    assert res["channel"] == "SMTP smtp.office365.com:587"

    with pytest.raises(FileNotFoundError, match="missing.csv"):
        _send({"to": "x@example.com", "dry_run": True, "attachments": ["./missing.csv"]}, tmp_path)


def test_missing_credentials_without_dry_run(no_smtp_env, tmp_path):
    with pytest.raises(ValueError, match="SMTP_USER and SMTP_PASSWORD"):
        _send({"to": "x@example.com"}, tmp_path)

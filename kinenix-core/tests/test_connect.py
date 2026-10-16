"""kinenix connect: the Hub this machine sends runs to, saved in kinenix.env and read by get_env."""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

from kinenix import connect, env, workspace
from kinenix.engine.redaction import Redactor


@pytest.fixture(autouse=True)
def settings(tmp_path, monkeypatch):
    """A fresh settings file and no Hub variables in the environment."""
    path = tmp_path / "kinenix.env"
    monkeypatch.setenv("KINENIX_SETTINGS_FILE", str(path))
    for name in ("KINENIX_HUB_URL", "KINENIX_HUB_API_KEY", "KINENIX_ORCHESTRATOR_URL", "KINENIX_ORCHESTRATOR_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(env, "_warned", set())
    return path


def _response(status):
    return MagicMock(status_code=status)


@pytest.mark.parametrize("text, expected", [
    ("192.168.1.137", "http://192.168.1.137:8080"),
    ("192.168.1.137:9000", "http://192.168.1.137:9000"),
    ("http://hub.local/", "http://hub.local:8080"),
    ("https://hub.example.com", "https://hub.example.com"),
    ("http://hub.local:8080", "http://hub.local:8080"),
])
def test_normalize_url(text, expected):
    assert connect.normalize_url(text) == expected


def test_normalize_url_rejects_other_schemes():
    with pytest.raises(ValueError):
        connect.normalize_url("ftp://hub")


def test_saved_settings_are_used_when_the_environment_has_none(monkeypatch):
    workspace.save_settings({"KINENIX_HUB_URL": "http://saved:8080", "KINENIX_HUB_API_KEY": "saved-key"})
    assert env.get_env("KINENIX_HUB_URL") == "http://saved:8080"
    assert env.env_source("KINENIX_HUB_URL") == "saved"
    monkeypatch.setenv("KINENIX_ORCHESTRATOR_URL", "http://legacy:8080")
    assert env.get_env("KINENIX_HUB_URL") == "http://legacy:8080"
    monkeypatch.setenv("KINENIX_HUB_URL", "http://env:8080")
    assert env.get_env("KINENIX_HUB_URL") == "http://env:8080"
    assert env.env_source("KINENIX_HUB_URL") == "environment"
    # An empty variable, as in a fresh worker.env (export KINENIX_HUB_URL=), does not hide the saved value
    monkeypatch.setenv("KINENIX_HUB_URL", "")
    monkeypatch.delenv("KINENIX_ORCHESTRATOR_URL")
    assert env.get_env("KINENIX_HUB_URL") == "http://saved:8080"


def test_save_settings_keeps_other_settings(settings, tmp_path):
    workspace.save_flows_dir(tmp_path / "flows")
    workspace.save_settings({"KINENIX_HUB_URL": "http://hub:8080", "KINENIX_HUB_API_KEY": "k" * 20})
    workspace.save_settings({"KINENIX_HUB_API_KEY": None})
    saved = workspace.saved_settings()
    assert saved == {"KINENIX_FLOWS_DIR": str((tmp_path / "flows").resolve()), "KINENIX_HUB_URL": "http://hub:8080"}
    if sys.platform != "win32":
        assert oct(os.stat(settings).st_mode & 0o777) == "0o600"


def test_the_saved_key_is_redacted():
    workspace.save_settings({"KINENIX_HUB_API_KEY": "saved-secret-key"})
    assert "saved-secret-key" not in str(Redactor().redact({"note": "key is saved-secret-key"}))


@pytest.mark.parametrize("status, usable, words", [
    (200, True, "accepts runs"),
    (404, True, "older version"),
    (401, False, "rejected the key"),
    (403, False, "no worker API key"),
])
def test_check(status, usable, words):
    with patch("kinenix.connect.requests.get", side_effect=[_response(200), _response(status)]) as get:
        result = connect.check("http://hub:8080", "key-1")
    assert result.usable is usable and words in result.message
    assert result.key_checked is (status != 404)
    assert get.call_args_list[1].kwargs["headers"] == {"X-API-Key": "key-1"}


def test_check_unreachable():
    with patch("kinenix.connect.requests.get", side_effect=requests.ConnectionError("down")),             patch("kinenix.connect.socket.getaddrinfo", return_value=[]):
        result = connect.check("http://hub:8080", None)
    assert not result.usable and "nothing accepts connections on port 8080" in result.message
    with patch("kinenix.connect.requests.get", side_effect=requests.Timeout("slow")),             patch("kinenix.connect.socket.getaddrinfo", return_value=[]):
        assert "firewall" in connect.check("http://hub:8080", None).message


def test_check_name_not_found():
    import socket
    with patch("kinenix.connect.requests.get", side_effect=requests.ConnectionError("dns")),             patch("kinenix.connect.socket.getaddrinfo", side_effect=socket.gaierror("no name")):
        message = connect.check("http://arttopix-black.local:8080", None).message
    assert "Cannot find the address of 'arttopix-black.local'" in message and "mDNS" in message


def test_saving_without_a_key_that_was_not_checked_warns(capsys):
    unchecked = connect.CheckResult(True, "older version", key_checked=False)
    with patch("kinenix.connect.check", return_value=unchecked):
        assert connect.connect("hub", None) == 0
    assert "no key was saved" in capsys.readouterr().out
    with patch("kinenix.connect.check", return_value=connect.CheckResult(True, "accepted")):
        assert connect.connect("hub", None) == 0
    assert "no key was saved" not in capsys.readouterr().out


def test_connect_saves_only_after_a_good_check(capsys):
    with patch("kinenix.connect.check", return_value=connect.CheckResult(False, "The Hub rejected the key.")):
        assert connect.connect("hub", "bad") == 1
    assert workspace.saved_settings() == {}
    assert "Nothing was saved" in capsys.readouterr().out

    with patch("kinenix.connect.check", return_value=connect.CheckResult(True, "The Hub accepts runs from this machine.")):
        assert connect.connect("hub", "good-key") == 0
    assert workspace.saved_settings() == {"KINENIX_HUB_URL": "http://hub:8080", "KINENIX_HUB_API_KEY": "good-key"}

    assert connect.connect("other:9000", None, verify=False) == 0
    assert workspace.saved_settings() == {"KINENIX_HUB_URL": "http://other:9000"}


def test_connect_warns_when_the_environment_wins(monkeypatch, capsys):
    monkeypatch.setenv("KINENIX_HUB_URL", "http://from-worker-env:8080")
    assert connect.connect("hub", None, verify=False) == 0
    assert "takes precedence" in capsys.readouterr().out


def test_show_and_disconnect(capsys):
    assert connect.show() == 0
    assert "Not connected" in capsys.readouterr().out
    workspace.save_settings({"KINENIX_HUB_URL": "http://hub:8080", "KINENIX_HUB_API_KEY": "key-12345"})
    with patch("kinenix.connect.check", return_value=connect.CheckResult(True, "The Hub accepts runs from this machine.")):
        assert connect.show() == 0
    out = capsys.readouterr().out
    assert "http://hub:8080" in out and "kinenix.env" in out and "key-12345" not in out
    assert connect.disconnect() == 0
    assert workspace.saved_settings() == {}


def test_telemetry_says_why_the_hub_was_not_reached(caplog):
    """A run whose Hub is down keeps its log and says why in plain words, as kinenix connect does."""
    from kinenix.engine.logger import ExecutionLogger
    from kinenix.models.context import ExecutionContext

    with patch("requests.post", side_effect=requests.ConnectionError("refused")), \
            patch("kinenix.connect.socket.getaddrinfo", return_value=[]), \
            caplog.at_level("WARNING", logger="kinenix"):
        ExecutionLogger(log_dir=None)._send_telemetry("http://hub.local:8080", {}, ExecutionContext(flow_name="x"))
    assert "The run was not sent to the Hub. hub.local was found, but nothing accepts connections on port 8080" in caplog.text
    assert "kept on this machine" in caplog.text

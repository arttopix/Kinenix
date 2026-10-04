"""Names from before the Orchestrator was renamed to Hub keep working in kinenix-core."""
import subprocess
import sys

from kinenix import env


def test_get_env_prefers_new_name_and_warns_once_for_old(monkeypatch, caplog):
    monkeypatch.setattr(env, "_warned", set())
    monkeypatch.delenv("KINENIX_HUB_URL", raising=False)
    monkeypatch.setenv("KINENIX_ORCHESTRATOR_URL", "http://old:8080")
    with caplog.at_level("WARNING", logger="kinenix"):
        assert env.get_env("KINENIX_HUB_URL") == "http://old:8080"
        assert env.get_env("KINENIX_HUB_URL") == "http://old:8080"
    assert caplog.text.count("KINENIX_ORCHESTRATOR_URL is deprecated") == 1

    monkeypatch.setenv("KINENIX_HUB_URL", "http://new:8080")
    assert env.get_env("KINENIX_HUB_URL") == "http://new:8080"
    monkeypatch.delenv("KINENIX_HUB_URL")
    monkeypatch.delenv("KINENIX_ORCHESTRATOR_URL")
    assert env.get_env("KINENIX_HUB_URL", "fallback") == "fallback"


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], capture_output=True, text=True, timeout=60)


def test_hub_command_and_legacy_alias():
    assert _cli("hub", "--help").returncode == 0
    assert "--no-prompt" in _cli("orchestrator", "--help").stdout
    assert "--orchestrator" in _cli("run", "--help").stdout

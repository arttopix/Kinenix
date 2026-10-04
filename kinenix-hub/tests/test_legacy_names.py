"""Names from before the Orchestrator was renamed to Hub keep working."""
import importlib

from kinenix_hub import config as hub_config
from kinenix_hub import settings_file
from kinenix_hub.settings_file import read_saved_settings, read_settings, write_settings

HUB_VARS = ("KINENIX_HUB_API_KEY", "KINENIX_HUB_PORT", "KINENIX_HUB_HOST", "KINENIX_HUB_DASHBOARD_PASSWORD")


def _reload(monkeypatch, **env):
    for name in HUB_VARS:
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.replace("KINENIX_HUB_", "ORCHESTRATOR_"), raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return importlib.reload(hub_config)


def test_legacy_environment_variables_are_used_and_reported(monkeypatch, caplog):
    try:
        cfg = _reload(monkeypatch, ORCHESTRATOR_API_KEY="old-key", ORCHESTRATOR_PORT="9100")
        assert (cfg.API_KEY, cfg.PORT) == ("old-key", 9100)
        assert set(cfg.LEGACY_NAMES_USED) == {"ORCHESTRATOR_API_KEY", "ORCHESTRATOR_PORT"}
        with caplog.at_level("WARNING"):
            cfg.log_legacy_names()
        assert "rename them to KINENIX_HUB_API_KEY, KINENIX_HUB_PORT" in caplog.text

        cfg = _reload(monkeypatch, ORCHESTRATOR_API_KEY="old-key", KINENIX_HUB_API_KEY="new-key")
        assert cfg.API_KEY == "new-key" and cfg.LEGACY_NAMES_USED == []
    finally:
        monkeypatch.undo()
        importlib.reload(hub_config)


def test_settings_file_with_legacy_keys(tmp_path):
    path = tmp_path / "orchestrator.env"
    path.write_text("ORCHESTRATOR_API_KEY=k\nORCHESTRATOR_PORT=9000\n", encoding="utf-8")
    assert read_settings(path) == {"KINENIX_HUB_API_KEY": "k", "KINENIX_HUB_PORT": "9000"}


def test_default_hub_env_falls_back_to_legacy_file_only_by_default(monkeypatch, tmp_path):
    default = tmp_path / "hub.env"
    legacy = tmp_path / "orchestrator.env"
    write_settings(legacy, {"ORCHESTRATOR_API_KEY": "from-legacy"})
    monkeypatch.setattr(settings_file, "DEFAULT_SETTINGS_FILE", default)
    monkeypatch.setattr(settings_file, "LEGACY_SETTINGS_FILE", legacy)

    assert read_saved_settings(default) == {"KINENIX_HUB_API_KEY": "from-legacy"}
    assert read_saved_settings(tmp_path / "custom.env") == {}  # an explicit file never falls back

    write_settings(default, {"KINENIX_HUB_API_KEY": "from-hub"})
    assert read_saved_settings(default) == {"KINENIX_HUB_API_KEY": "from-hub"}

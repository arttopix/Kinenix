import importlib

from fastapi.testclient import TestClient

from kinenix_orchestrator import config as orchestrator_config
from kinenix_orchestrator.app import app
from kinenix_orchestrator.settings_file import hash_password, read_settings, verify_password, write_settings

remote_client = TestClient(app, client=("192.168.1.77", 50000))


def test_password_hash_roundtrip():
    stored = hash_password("s3cret")
    assert stored.startswith("pbkdf2_sha256$")
    assert "s3cret" not in stored
    assert verify_password("s3cret", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("s3cret", "garbage")
    assert hash_password("s3cret") != stored  # salted


def test_read_and_write_settings(tmp_path):
    path = tmp_path / "sub" / "orchestrator.env"
    assert read_settings(path) == {}
    write_settings(path, {"ORCHESTRATOR_PORT": "9000", "ORCHESTRATOR_API_KEY": "k=with=equals", "EMPTY": ""})
    assert read_settings(path) == {"ORCHESTRATOR_PORT": "9000", "ORCHESTRATOR_API_KEY": "k=with=equals"}
    assert path.read_text(encoding="utf-8").startswith("# Kinenix Orchestrator settings")


def test_environment_overrides_saved_settings(monkeypatch, tmp_path):
    path = tmp_path / "orchestrator.env"
    write_settings(path, {"ORCHESTRATOR_HOST": "0.0.0.0", "ORCHESTRATOR_PORT": "9000",
                          "ORCHESTRATOR_API_KEY": "saved-key",
                          "ORCHESTRATOR_DASHBOARD_PASSWORD_HASH": hash_password("pw")})
    monkeypatch.setenv("ORCHESTRATOR_SETTINGS_FILE", str(path))
    for name in ("ORCHESTRATOR_HOST", "ORCHESTRATOR_PORT", "ORCHESTRATOR_API_KEY", "ORCHESTRATOR_DASHBOARD_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    try:
        cfg = importlib.reload(orchestrator_config)
        assert (cfg.HOST, cfg.PORT, cfg.API_KEY) == ("0.0.0.0", 9000, "saved-key")
        assert cfg.dashboard_password_required()

        monkeypatch.setenv("ORCHESTRATOR_PORT", "7000")
        monkeypatch.setenv("ORCHESTRATOR_DASHBOARD_PASSWORD", "plain")
        cfg = importlib.reload(orchestrator_config)
        assert cfg.PORT == 7000
        assert cfg.DASHBOARD_PASSWORD == "plain" and cfg.DASHBOARD_PASSWORD_HASH == ""
    finally:
        monkeypatch.undo()
        importlib.reload(orchestrator_config)


def test_dashboard_accepts_saved_password_hash(monkeypatch):
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_USER", "admin")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD", "")
    monkeypatch.setattr(orchestrator_config, "DASHBOARD_PASSWORD_HASH", hash_password("pw"))

    assert remote_client.get("/api/v1/workers").status_code == 401
    assert remote_client.get("/api/v1/workers", auth=("admin", "wrong")).status_code == 401
    assert remote_client.get("/api/v1/workers", auth=("admin", "pw")).status_code == 200
    # Second request uses the cached verification and must still succeed
    assert remote_client.get("/api/v1/workers", auth=("admin", "pw")).status_code == 200
    assert remote_client.get("/api/v1/workers", auth=("other", "pw")).status_code == 401

import os
from pathlib import Path

from .settings_file import read_settings, settings_path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Values saved by `kinenix orchestrator setup`; environment variables take precedence over them
SETTINGS_FILE = settings_path()
_saved = read_settings(SETTINGS_FILE)


def _setting(name: str, default: str) -> str:
    return os.environ.get(name) or _saved.get(name) or default


# Database configuration: defaults to SQLite file; easily overridden by setting DATABASE_URL (e.g. PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/orchestrator.db")

# Central LLM Endpoint (OpenThai-SystemOne server on port 8000)
CENTRAL_LLM_URL = os.environ.get("CENTRAL_LLM_URL", "http://127.0.0.1:8000/v1/systemone")

# Server binding: localhost by default; set ORCHESTRATOR_HOST=0.0.0.0 to accept remote workers and viewers
HOST = _setting("ORCHESTRATOR_HOST", "127.0.0.1")
PORT = int(_setting("ORCHESTRATOR_PORT", "8080"))

# Shared secret that workers must send in the X-API-Key header; when unset, only localhost clients may write
API_KEY = _setting("ORCHESTRATOR_API_KEY", "")

# HTTP Basic Auth for the dashboard page and read endpoints; when no password is set, only localhost may view.
# The settings file stores only a hash; ORCHESTRATOR_DASHBOARD_PASSWORD from the environment takes precedence.
DASHBOARD_USER = _setting("ORCHESTRATOR_DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.environ.get("ORCHESTRATOR_DASHBOARD_PASSWORD", "")
DASHBOARD_PASSWORD_HASH = "" if DASHBOARD_PASSWORD else _saved.get("ORCHESTRATOR_DASHBOARD_PASSWORD_HASH", "")

# A worker with no heartbeat for this many seconds is reported as offline
WORKER_OFFLINE_SECONDS = int(os.environ.get("ORCHESTRATOR_WORKER_OFFLINE_SECONDS", "90"))

# Static and artifacts directory
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def dashboard_password_required() -> bool:
    return bool(DASHBOARD_PASSWORD or DASHBOARD_PASSWORD_HASH)

import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Database configuration: defaults to SQLite file; easily overridden by setting DATABASE_URL (e.g. PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/orchestrator.db")

# Central LLM Endpoint (OpenThai-SystemOne server on port 8000)
CENTRAL_LLM_URL = os.environ.get("CENTRAL_LLM_URL", "http://127.0.0.1:8000/v1/systemone")

# Server binding: localhost by default; set ORCHESTRATOR_HOST=0.0.0.0 to accept remote workers and viewers
HOST = os.environ.get("ORCHESTRATOR_HOST", "127.0.0.1")
PORT = int(os.environ.get("ORCHESTRATOR_PORT", "8080"))

# Shared secret that workers must send in the X-API-Key header; when unset, only localhost clients may write
API_KEY = os.environ.get("ORCHESTRATOR_API_KEY", "")

# HTTP Basic Auth for the dashboard page and read endpoints; when the password is unset, only localhost may view
DASHBOARD_USER = os.environ.get("ORCHESTRATOR_DASHBOARD_USER", "admin")
DASHBOARD_PASSWORD = os.environ.get("ORCHESTRATOR_DASHBOARD_PASSWORD", "")

# Static and artifacts directory
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


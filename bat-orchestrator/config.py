import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Database configuration: defaults to SQLite file; easily overridden by setting DATABASE_URL (e.g. PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/orchestrator.db")

# Central LLM Endpoint (OpenThai-SystemOne server on port 8000)
CENTRAL_LLM_URL = os.environ.get("CENTRAL_LLM_URL", "http://127.0.0.1:8000/v1/systemone")

# Server binding
HOST = os.environ.get("ORCHESTRATOR_HOST", "0.0.0.0")
PORT = int(os.environ.get("ORCHESTRATOR_PORT", "8080"))

# Static and artifacts directory
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


"""Saved Orchestrator settings in the user's home directory, written by `kinenix orchestrator setup`.

The file lives outside the repository (default ~/.kinenix/orchestrator.env, override with
ORCHESTRATOR_SETTINGS_FILE) and holds plain KEY=VALUE lines. Environment variables always take
precedence over it. The dashboard password is stored only as a salted PBKDF2 hash.
"""
import base64
import hashlib
import hmac
import os
import secrets
from pathlib import Path
from typing import Dict

PBKDF2_ITERATIONS = 300_000


def settings_path() -> Path:
    override = os.environ.get("ORCHESTRATOR_SETTINGS_FILE")
    return Path(override).expanduser() if override else Path.home() / ".kinenix" / "orchestrator.env"


def read_settings(path: Path) -> Dict[str, str]:
    if not path.is_file():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def write_settings(path: Path, values: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Kinenix Orchestrator settings, written by `kinenix orchestrator setup`.",
             "# Environment variables with the same names take precedence. Do not commit this file."]
    lines += [f"{key}={value}" for key, value in values.items() if value != ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)  # owner-only on Linux and macOS; Windows keeps the home directory's ACL
    except OSError:
        pass


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    encode = lambda b: base64.b64encode(b).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${encode(salt)}${encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.b64decode(salt), int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, base64.b64decode(expected))

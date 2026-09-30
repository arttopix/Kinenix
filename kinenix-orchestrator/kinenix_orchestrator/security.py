import ipaddress
import logging
import secrets
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials

from . import config

logger = logging.getLogger("kinenix.orchestrator.security")

API_KEY_HEADER_NAME = "X-API-Key"
DASHBOARD_REALM = "Kinenix Orchestrator"

_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
_basic_auth = HTTPBasic(auto_error=False, realm=DASHBOARD_REALM)


def _is_loopback(host: Optional[str]) -> bool:
    if not host:
        return False
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def _secret_equals(provided: Optional[str], expected: str) -> bool:
    if provided is None:
        return False
    return secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def _allow_loopback_only(request: Request, setting_name: str) -> None:
    client_host = request.client.host if request.client else None
    if _is_loopback(client_host):
        return
    logger.warning(f"Rejected request from {client_host}: {setting_name} is not configured.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Remote access is disabled. Set {setting_name} on the Orchestrator to allow remote access.",
    )


def require_worker_api_key(
    request: Request,
    api_key: Optional[str] = Security(_api_key_header),
) -> None:
    """
    Guards worker-facing write endpoints (heartbeat, telemetry, reanalyze).

    - ORCHESTRATOR_API_KEY set: every request must send a matching X-API-Key header.
    - ORCHESTRATOR_API_KEY unset (local dev mode): only loopback clients are accepted,
      so an unconfigured server bound to the network (e.g. 0.0.0.0) is never writable remotely.
    """
    expected_key = config.API_KEY

    if not expected_key:
        _allow_loopback_only(request, "ORCHESTRATOR_API_KEY")
        return

    if not _secret_equals(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def require_dashboard_auth(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Security(_basic_auth),
) -> None:
    """
    Guards the dashboard page and its read endpoints with HTTP Basic Auth.

    - ORCHESTRATOR_DASHBOARD_PASSWORD set: every request must send matching Basic credentials.
      Browsers show a login prompt and reuse the credentials for the dashboard's API calls.
    - ORCHESTRATOR_DASHBOARD_PASSWORD unset (local dev mode): only loopback clients are accepted.
    """
    expected_password = config.DASHBOARD_PASSWORD

    if not expected_password:
        _allow_loopback_only(request, "ORCHESTRATOR_DASHBOARD_PASSWORD")
        return

    # Evaluate both comparisons so the response time does not reveal which one failed
    user_ok = _secret_equals(credentials.username if credentials else None, config.DASHBOARD_USER)
    password_ok = _secret_equals(credentials.password if credentials else None, expected_password)
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing dashboard credentials.",
            headers={"WWW-Authenticate": f'Basic realm="{DASHBOARD_REALM}"'},
        )


def log_auth_mode() -> None:
    if config.API_KEY:
        logger.info(f"Worker API key authentication enabled ({API_KEY_HEADER_NAME} header required).")
    else:
        logger.warning(
            "ORCHESTRATOR_API_KEY is not set: worker endpoints accept requests from localhost only. "
            "Set ORCHESTRATOR_API_KEY to allow remote workers."
        )

    if config.DASHBOARD_PASSWORD:
        logger.info(f"Dashboard authentication enabled (user '{config.DASHBOARD_USER}').")
    else:
        logger.warning(
            "ORCHESTRATOR_DASHBOARD_PASSWORD is not set: the dashboard is available from localhost only. "
            "Set ORCHESTRATOR_DASHBOARD_PASSWORD to allow remote viewers."
        )

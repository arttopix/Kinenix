from pathlib import Path
from typing import Any, Dict
import requests

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


@register_action("http.request")
class HttpRequestAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        url = parameters.get("url")
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        payload = parameters.get("payload")
        timeout = parameters.get("timeout", 30)

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload if isinstance(payload, dict) else None,
            data=payload if isinstance(payload, str) else None,
            timeout=timeout
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body
        }


@register_action("http.download")
class HttpDownloadAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        url = parameters.get("url")
        target_path_str = parameters.get("target_path")
        timeout = float(parameters.get("timeout", 60))

        if not url:
            raise ValueError("Parameter 'url' is required for action 'http.download'.")
        if not target_path_str:
            raise ValueError("Parameter 'target_path' is required for action 'http.download'.")

        target_path = Path(target_path_str)
        if not target_path.is_absolute():
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                target_path = Path(flow_dir_str) / target_path_str

        target_path.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = target_path.stat().st_size
        return {
            "status": "downloaded",
            "file_path": str(target_path),
            "file_size": file_size
        }


import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ..env import get_env
from ..models.context import ExecutionContext, StepResult


def resolve_log_dir(log_dir: Optional[Union[str, Path]] = None, flow_path: Optional[Path] = None) -> Path:
    """
    Smart Log Directory Resolver:
    Locates the project root (containing .git or kinenix-core) so logs are always saved to
    the root 'logs/' directory, regardless of whether called from kinenix-core or another subfolder.
    """
    if log_dir and str(log_dir).strip() not in ["", "logs"]:
        return Path(log_dir).resolve()

    if os.getenv("KINENIX_LOG_DIR"):
        return Path(os.environ["KINENIX_LOG_DIR"]).resolve()

    # 1. Search upwards from Current Working Directory
    curr = Path.cwd().resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").exists() or (p / "kinenix-core").is_dir():
            return p / "logs"

    # 2. Search upwards from flow file if provided
    if flow_path:
        f_resolved = Path(flow_path).resolve()
        for p in list(f_resolved.parents):
            if (p / ".git").exists() or (p / "kinenix-core").is_dir():
                return p / "logs"

    # 3. Fallback to CWD/logs
    return (Path.cwd() / "logs").resolve()


class ExecutionLogger:
    """
    Structured logger for recording flow execution steps and metrics.
    Prints to console and outputs structured JSON logs.
    """

    def __init__(self, log_dir: Optional[Union[str, Path]] = None, flow_path: Optional[Path] = None):
        self.logger = logging.getLogger("kinenix")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        if not log_dir and "PYTEST_CURRENT_TEST" in os.environ:
            self.log_dir = Path(tempfile.gettempdir()) / "kinenix_test_logs"
        else:
            self.log_dir = resolve_log_dir(log_dir, flow_path=flow_path)

        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


    def log_step_start(self, step_id: str, step_name: str, action: str) -> None:
        self.logger.info(f"Starting Step [{step_id}] '{step_name}' (Action: {action})")

    def log_step_result(self, result: StepResult) -> None:
        status_upper = result.status.upper()
        if result.status == "success":
            self.logger.info(
                f"Completed Step [{result.step_id}] '{result.step_name}' in {result.duration_seconds:.3f}s"
            )
        elif result.status == "failed":
            self.logger.error(
                f"Failed Step [{result.step_id}] '{result.step_name}' - [{result.error_type} Error]: {result.error_message}"
            )
        else:
            self.logger.warning(f"Skipped Step [{result.step_id}] '{result.step_name}'")

    def log_execution_summary(self, context: ExecutionContext) -> None:
        m = context.metrics
        self.logger.info("=== Flow Execution Summary ===")
        self.logger.info(f"Flow Name: {context.flow_name}")
        self.logger.info(f"Total Steps: {m.total_steps} (Success: {m.successful_steps}, Failed: {m.failed_steps}, Skipped: {m.skipped_steps})")
        self.logger.info(f"Total Duration: {m.total_duration_seconds:.2f}s")

        raw_data = context.model_dump(mode="python")
        raw_data = {"$schema": "../../../schemas/execution_log.schema.json", **raw_data}

        # Filter out internal private runtime variables (e.g. __playwright_*)
        if "variables" in raw_data and isinstance(raw_data["variables"], dict):
            raw_data["variables"] = {
                k: v for k, v in raw_data["variables"].items() if not str(k).startswith("__")
            }

        if self.log_dir:
            try:
                import re
                flow_slug = re.sub(r"[^\w\-]+", "_", context.flow_name.lower().strip()).strip("_")
                date_str = context.start_time.strftime("%Y-%m-%d")
                time_str = context.start_time.strftime("%H%M%S")
                status_str = "failed" if context.has_error else "success"

                target_dir = self.log_dir / flow_slug / date_str
                target_dir.mkdir(parents=True, exist_ok=True)

                log_file = target_dir / f"{time_str}_{status_str}.json"
                log_file.write_text(json.dumps(raw_data, default=str, indent=2, ensure_ascii=False), encoding="utf-8")
                self.logger.info(f"Saved JSON log to: {log_file}")
            except Exception as e:
                self.logger.error(f"Failed to save JSON execution log: {e}")

        # Send telemetry to the Hub if configured, whether or not a log file is written
        hub_url = (
            context.get_variable("hub_url")
            or context.get_variable("orchestrator_url")  # flow variable name before the rename to Hub
            or context.get_variable("telemetry_url")
            or get_env("KINENIX_HUB_URL")
        )
        if hub_url:
            self._send_telemetry(hub_url, raw_data, context)

    def _send_telemetry(self, hub_url: str, raw_data: dict, context: ExecutionContext) -> None:
        try:
            import requests
            worker_id = (
                context.get_variable("worker_id")
                or os.environ.get("KINENIX_WORKER_ID")
                or "local-worker"
            )
            clean_url = str(hub_url).rstrip("/")
            target_endpoint = f"{clean_url}/api/v1/telemetry"
            # Round-trip through JSON with the same datetime handling as the log file,
            # since requests' json= encoder cannot serialize datetime values
            payload = {
                "worker_id": worker_id,
                "payload": json.loads(json.dumps(raw_data, default=str))
            }
            headers = {}
            api_key = get_env("KINENIX_HUB_API_KEY")
            if api_key:
                headers["X-API-Key"] = api_key
            res = requests.post(target_endpoint, json=payload, headers=headers, timeout=4)
            if res.status_code == 200:
                self.logger.info(f"Transmitted telemetry to Hub: {clean_url}")
            elif res.status_code in (401, 403):
                self.logger.warning(
                    f"Hub rejected telemetry (HTTP {res.status_code}). "
                    "Check that KINENIX_HUB_API_KEY on this worker has the same value as on the Hub."
                )
            else:
                self.logger.warning(f"Hub returned HTTP {res.status_code}: {res.text}")
        except Exception as err:
            self.logger.warning(f"Telemetry transmission to Hub failed: {err}")


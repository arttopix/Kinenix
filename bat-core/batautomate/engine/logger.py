import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ..models.context import ExecutionContext, StepResult


def resolve_log_dir(log_dir: Optional[Union[str, Path]] = None, flow_path: Optional[Path] = None) -> Path:
    """
    Smart Log Directory Resolver:
    Locates the project root (containing .git or bat-core) so logs are always saved to
    the root 'logs/' directory, regardless of whether called from bat-core or another subfolder.
    """
    if log_dir and str(log_dir).strip() not in ["", "logs"]:
        return Path(log_dir).resolve()

    if os.getenv("BAT_LOG_DIR"):
        return Path(os.environ["BAT_LOG_DIR"]).resolve()

    # 1. Search upwards from Current Working Directory
    curr = Path.cwd().resolve()
    for p in [curr] + list(curr.parents):
        if (p / ".git").exists() or (p / "bat-core").is_dir():
            return p / "logs"

    # 2. Search upwards from flow file if provided
    if flow_path:
        f_resolved = Path(flow_path).resolve()
        for p in list(f_resolved.parents):
            if (p / ".git").exists() or (p / "bat-core").is_dir():
                return p / "logs"

    # 3. Fallback to CWD/logs
    return (Path.cwd() / "logs").resolve()


class ExecutionLogger:
    """
    Structured logger for recording flow execution steps and metrics.
    Prints to console and outputs structured JSON logs.
    """

    def __init__(self, log_dir: Optional[Union[str, Path]] = None, flow_path: Optional[Path] = None):
        self.logger = logging.getLogger("batautomate")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        if not log_dir and "PYTEST_CURRENT_TEST" in os.environ:
            self.log_dir = Path(tempfile.gettempdir()) / "batautomate_test_logs"
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

        if self.log_dir:
            try:
                raw_data = context.model_dump(mode="python")
                raw_data = {"$schema": "../../../schemas/execution_log.schema.json", **raw_data}

                # Filter out internal private runtime variables (e.g. __playwright_*)
                if "variables" in raw_data and isinstance(raw_data["variables"], dict):
                    raw_data["variables"] = {
                        k: v for k, v in raw_data["variables"].items() if not str(k).startswith("__")
                    }

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

                # Send telemetry to Central Orchestrator if configured
                orchestrator_url = (
                    context.get_variable("orchestrator_url")
                    or context.get_variable("telemetry_url")
                    or os.environ.get("BATAUTOMATE_ORCHESTRATOR_URL")
                )
                if orchestrator_url:
                    self._send_telemetry(orchestrator_url, raw_data, context)
            except Exception as e:
                self.logger.error(f"Failed to save JSON execution log: {e}")

    def _send_telemetry(self, orchestrator_url: str, raw_data: dict, context: ExecutionContext) -> None:
        try:
            import requests
            worker_id = (
                context.get_variable("worker_id")
                or os.environ.get("BATAUTOMATE_WORKER_ID")
                or "local-worker"
            )
            clean_url = str(orchestrator_url).rstrip("/")
            target_endpoint = f"{clean_url}/api/v1/telemetry"
            payload = {
                "worker_id": worker_id,
                "payload": raw_data
            }
            res = requests.post(target_endpoint, json=payload, timeout=4)
            if res.status_code == 200:
                self.logger.info(f"Transmitted telemetry to Orchestrator: {clean_url}")
            else:
                self.logger.warning(f"Orchestrator returned HTTP {res.status_code}: {res.text}")
        except Exception as err:
            self.logger.debug(f"Telemetry transmission skipped: {err}")


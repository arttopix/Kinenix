import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from ..models import Execution, Worker
from ..timeutils import parse_timestamp, utc_now
from .ai_summarizer import analyze_failure

logger = logging.getLogger("kinenix.hub.telemetry")


def record_heartbeat(
    db: Session,
    worker_id: str,
    name: str,
    ip_address: str,
    os_info: str,
    cpu_percent: float,
    ram_usage: str,
    current_task: str = None
) -> Worker:
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        worker = Worker(id=worker_id, name=name)
        db.add(worker)

    worker.name = name
    worker.ip_address = ip_address
    worker.os_info = os_info
    worker.cpu_percent = cpu_percent
    worker.ram_usage = ram_usage
    worker.current_task = current_task
    worker.status = "busy" if current_task else "online"
    worker.last_heartbeat = utc_now()
    db.commit()
    db.refresh(worker)
    return worker


# Step fields safe to show in the dashboard and CLI. Step output and flow variables are left out
# because they can carry business data (form values, extracted documents, credentials in URLs).
STEP_FIELDS = ("step_id", "step_name", "action", "status", "start_time", "end_time",
               "duration_seconds", "error_type", "error_message")


def step_summaries(raw_log: Optional[str]) -> List[Dict[str, Any]]:
    """Per-step results from a stored execution log, reduced to STEP_FIELDS. Empty if unavailable."""
    if not raw_log:
        return []
    try:
        steps = json.loads(raw_log).get("step_results") or []
    except (ValueError, AttributeError):
        return []
    return [{field: step.get(field) for field in STEP_FIELDS} for step in steps if isinstance(step, dict)]


def ingest_execution_log(db: Session, payload: Dict[str, Any], worker_id: str = "local-worker") -> Execution:
    flow_name = payload.get("flow_name", "Unknown Flow")
    has_error = bool(payload.get("has_error", False))
    failure_details = payload.get("failure_details") or {}
    metrics = payload.get("metrics") or {}

    start_time_str = payload.get("start_time")
    end_time_str = payload.get("end_time")

    duration = float(metrics.get("total_duration_seconds", 0.0))

    # Execution logs from kinenix-core carry start_time and a duration but no end_time
    start_time = parse_timestamp(start_time_str) or utc_now()
    end_time = parse_timestamp(end_time_str) or (start_time + datetime.timedelta(seconds=duration))

    execution = Execution(
        worker_id=worker_id,
        flow_name=flow_name,
        status="failed" if has_error else "success",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        has_error=has_error,
        raw_log=json.dumps(payload, ensure_ascii=False)
    )

    if has_error:
        execution.failed_step_id = failure_details.get("failed_step_id")
        execution.failed_step_name = failure_details.get("failed_step_name")
        execution.error_type = failure_details.get("error_type")
        execution.exception_class = failure_details.get("exception_class")
        execution.error_message = failure_details.get("error_message")
        execution.screenshot_path = failure_details.get("screenshot_path")

        # Run AI Triage & Summarization
        ai_res = analyze_failure(
            flow_name=flow_name,
            failed_step_name=execution.failed_step_name,
            error_message=execution.error_message,
            exception_class=execution.exception_class
        )
        execution.ai_category = ai_res.get("category")
        execution.ai_confidence = ai_res.get("confidence")
        execution.ai_summary = ai_res.get("summary")
        execution.ai_root_cause = ai_res.get("root_cause")
        execution.ai_suggestion = ai_res.get("suggestion")

    db.add(execution)
    db.commit()
    db.refresh(execution)

    # Update worker's current task
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if worker:
        worker.current_task = None
        worker.status = "online"
        db.commit()

    return execution


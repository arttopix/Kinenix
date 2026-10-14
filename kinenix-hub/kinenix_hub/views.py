"""Views over the run records, so people and AI query one flat table instead of JSON (docs/hub_data.md).

Views hold no data, so the Hub drops and creates them at every start instead of changing them through
migrations. Kinenix view names start with `v_`; user views (`custom_`) are never touched here.
The views read JSON with SQLite's json_extract; on another database they are not created.
"""
import logging
from typing import Dict

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("kinenix.hub")


def _json(column: str, path: str, name: str) -> str:
    return f"json_extract({column}, '$.{path}') AS {name}"


VIEWS: Dict[str, str] = {
    "v_runs": f"""
SELECT
    e.id AS execution_id,
    {_json("e.details", "run_id", "run_id")},
    e.flow_name,
    e.worker_id,
    e.status,
    e.start_time AS started_at,
    e.end_time AS ended_at,
    e.duration_seconds,
    {_json("e.details", "kinenix_version", "kinenix_version")},
    {_json("e.details", "items_total", "items_total")},
    {_json("e.details", "items_done", "items_done")},
    {_json("e.details", "items_failed", "items_failed")},
    (SELECT COUNT(*) FROM step_results s WHERE s.execution_id = e.id) AS step_count,
    (SELECT COUNT(*) FROM failures f WHERE f.execution_id = e.id) AS failure_count,
    e.failed_step_name,
    e.error_type,
    e.error_message,
    {_json("e.details", "report_md", "report_md")}
FROM executions e
""",
    "v_failures": f"""
SELECT
    f.id AS failure_id,
    f.execution_id,
    {_json("e.details", "run_id", "run_id")},
    f.failed_at,
    f.flow_name,
    f.worker_id,
    {_json("f.details", "section", "section")},
    f.step_name,
    f.action,
    {_json("f.details", "path", "step_path")},
    {_json("f.details", "subflow", "subflow")},
    {_json("f.details", "line", "line")},
    {_json("f.details", "loop.item", "loop_item")},
    {_json("f.details", "loop.index", "loop_index")},
    {_json("f.details", "loop.of", "loop_of")},
    {_json("f.details", "retries", "retries")},
    f.handled,
    f.error_type,
    {_json("f.details", "exception", "exception")},
    f.message,
    {_json("f.details", "root_cause", "root_cause")},
    {_json("f.details", "suggested_fix", "suggested_fix")},
    {_json("f.details", "screenshot", "screenshot")},
    e.status AS run_status
FROM failures f
LEFT JOIN executions e ON e.id = f.execution_id
""",
    "v_steps": f"""
SELECT
    s.id AS step_result_id,
    s.execution_id,
    {_json("e.details", "run_id", "run_id")},
    e.flow_name,
    e.worker_id,
    s.seq,
    s.section,
    s.step_id,
    s.step_name,
    s.action,
    s.status,
    s.started_at,
    s.duration_seconds,
    {_json("s.details", "path", "step_path")},
    {_json("s.details", "subflow", "subflow")},
    {_json("s.details", "line", "line")},
    {_json("s.details", "loop.item", "loop_item")},
    {_json("s.details", "loop.index", "loop_index")},
    {_json("s.details", "loop.of", "loop_of")},
    {_json("s.details", "retries", "retries")},
    {_json("s.details", "skipped_reason", "skipped_reason")},
    {_json("s.details", "error", "error")},
    {_json("s.details", "output", "output")}
FROM step_results s
LEFT JOIN executions e ON e.id = s.execution_id
""",
}


def create_views(engine: Engine) -> None:
    """Drops and creates the Kinenix views, so they always match this Hub version."""
    if engine.dialect.name != "sqlite":
        logger.warning("Hub views (v_runs, v_failures, v_steps) are only created on SQLite.")
        return
    with engine.begin() as conn:
        for name, select in VIEWS.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            conn.execute(text(f"CREATE VIEW {name} AS {select.strip()}"))

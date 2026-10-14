"""Schema migrations: an existing hub.db is upgraded in place at start, and nothing is lost."""
import json

import pytest
from sqlalchemy import create_engine, inspect, text

from kinenix_hub import database, models  # noqa: F401  (models registers the tables on Base)
from kinenix_hub.database import Base
from kinenix_hub.migrations import (
    MIGRATIONS,
    Migration,
    add_column_if_missing,
    applied_versions,
    current_version,
    run_migrations,
)


def _engine(path):
    return create_engine(f"sqlite:///{path.as_posix()}")


# The number after the last real migration, for migrations made up by a test
NEXT = MIGRATIONS[-1].number + 1


def _legacy_hub_db(path):
    """A database as Hub 0.2.0b3 left it: workers and executions without details, a row, and no schema_version."""
    engine = _engine(path)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE failures"))
        conn.execute(text("DROP TABLE step_results"))
        conn.execute(text("ALTER TABLE executions DROP COLUMN details"))
        conn.execute(text("INSERT INTO executions (id, worker_id, flow_name, status) VALUES ('run-1', 'rpi4', 'TIPH', 'failed')"))
    return engine


def test_new_database_records_every_migration_once(tmp_path):
    engine = _engine(tmp_path / "new.db")
    Base.metadata.create_all(bind=engine)
    assert run_migrations(engine) == [m.number for m in MIGRATIONS]
    assert current_version(engine) == MIGRATIONS[-1].number
    assert run_migrations(engine) == []


def test_existing_database_is_upgraded_and_keeps_its_data(tmp_path):
    engine = _legacy_hub_db(tmp_path / "hub.db")
    assert applied_versions(engine) == []

    add_note = Migration(NEXT, "executions.note", lambda c: add_column_if_missing(c, "executions", "note", "TEXT"))
    assert run_migrations(engine, MIGRATIONS + [add_note]) == [m.number for m in MIGRATIONS] + [NEXT]

    columns = {c["name"] for c in inspect(engine).get_columns("executions")}
    assert {"details", "note"} <= columns
    assert {"step_results", "failures"} <= set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        assert conn.execute(text("SELECT flow_name, status FROM executions")).all() == [("TIPH", "failed")]
    assert run_migrations(engine, MIGRATIONS + [add_note]) == []


def test_adding_a_column_that_create_all_already_made_is_harmless(tmp_path):
    engine = _engine(tmp_path / "new.db")
    Base.metadata.create_all(bind=engine)
    add_again = Migration(NEXT, "executions.status again", lambda c: add_column_if_missing(c, "executions", "status", "TEXT"))
    assert run_migrations(engine, MIGRATIONS + [add_again]) == [m.number for m in MIGRATIONS] + [NEXT]


def test_a_failing_migration_changes_nothing_and_is_not_recorded(tmp_path):
    engine = _legacy_hub_db(tmp_path / "hub.db")

    def half_done(conn):
        add_column_if_missing(conn, "executions", "half", "TEXT")
        raise RuntimeError("step failed halfway")

    with pytest.raises(RuntimeError, match="halfway"):
        run_migrations(engine, MIGRATIONS + [Migration(NEXT, "broken", half_done)])
    assert applied_versions(engine) == [m.number for m in MIGRATIONS]
    assert "half" not in {c["name"] for c in inspect(engine).get_columns("executions")}


def test_runs_stored_before_the_upgrade_get_their_records(tmp_path):
    engine = _legacy_hub_db(tmp_path / "hub.db")
    old_log = {
        "flow_name": "TIPH", "has_error": True,
        "failure_details": {"failed_step_id": "s2", "failed_step_name": "Submit", "exception_class": "TimeoutError",
                            "error_message": "Timeout"},
        "step_results": [
            {"step_id": "s1", "step_name": "Open", "action": "web.open", "status": "success", "duration_seconds": 1.0},
            {"step_id": "s2", "step_name": "Submit", "action": "web.click", "status": "failed",
             "duration_seconds": 2.0, "error_message": "Timeout", "error_type": "Technical"},
        ],
    }
    with engine.begin() as conn:
        conn.execute(text("UPDATE executions SET raw_log = :log, has_error = 1 WHERE id = 'run-1'"),
                     {"log": json.dumps(old_log)})
        # A run without a usable log keeps what its columns say
        conn.execute(text("INSERT INTO executions (id, worker_id, flow_name, status, has_error, failed_step_name, error_message, raw_log)"
                          " VALUES ('run-2', 'rpi4', 'TIPH', 'failed', 1, 'Login', 'Wrong password', 'not json')"))

    run_migrations(engine)

    with engine.connect() as conn:
        steps = conn.execute(text("SELECT execution_id, seq, step_name, status FROM step_results ORDER BY execution_id, seq")).all()
        failures = conn.execute(text("SELECT execution_id, step_name, handled, message FROM failures ORDER BY execution_id")).all()
        details = dict(conn.execute(text("SELECT id, details FROM executions")).all())
    assert steps == [("run-1", 1, "Open", "success"), ("run-1", 2, "Submit", "failed")]
    assert failures == [("run-1", "Submit", "stopped", "Timeout"), ("run-2", "Login", "stopped", "Wrong password")]
    assert '"Login"' in json.loads(details["run-2"])["report_md"]
    assert all(json.loads(d)["v"] == 1 for d in details.values())


def test_hub_database_runs_in_wal_mode():
    database.init_db()
    with database.engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 5000
    assert current_version(database.engine) == MIGRATIONS[-1].number

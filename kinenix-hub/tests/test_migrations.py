"""Schema migrations: an existing hub.db is upgraded in place at start, and nothing is lost."""
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


def _legacy_hub_db(path):
    """A database as an older Hub left it: tables from create_all, a row, and no schema_version."""
    engine = _engine(path)
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
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

    add_details = Migration(2, "executions.details", lambda c: add_column_if_missing(c, "executions", "details", "TEXT"))
    assert run_migrations(engine, MIGRATIONS + [add_details]) == [1, 2]

    columns = {c["name"] for c in inspect(engine).get_columns("executions")}
    assert "details" in columns
    with engine.connect() as conn:
        assert conn.execute(text("SELECT flow_name, status FROM executions")).all() == [("TIPH", "failed")]
    assert run_migrations(engine, MIGRATIONS + [add_details]) == []


def test_adding_a_column_that_create_all_already_made_is_harmless(tmp_path):
    engine = _engine(tmp_path / "new.db")
    Base.metadata.create_all(bind=engine)
    add_again = Migration(2, "executions.status again", lambda c: add_column_if_missing(c, "executions", "status", "TEXT"))
    assert run_migrations(engine, MIGRATIONS + [add_again]) == [1, 2]


def test_a_failing_migration_changes_nothing_and_is_not_recorded(tmp_path):
    engine = _legacy_hub_db(tmp_path / "hub.db")

    def half_done(conn):
        add_column_if_missing(conn, "executions", "half", "TEXT")
        raise RuntimeError("step failed halfway")

    with pytest.raises(RuntimeError, match="halfway"):
        run_migrations(engine, MIGRATIONS + [Migration(2, "broken", half_done)])
    assert applied_versions(engine) == [1]
    assert "half" not in {c["name"] for c in inspect(engine).get_columns("executions")}


def test_hub_database_runs_in_wal_mode():
    database.init_db()
    with database.engine.connect() as conn:
        assert conn.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert conn.execute(text("PRAGMA busy_timeout")).scalar() == 5000
    assert current_version(database.engine) == MIGRATIONS[-1].number

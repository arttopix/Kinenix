"""Schema changes for an existing Hub database, applied in order when the Hub starts.

`Base.metadata.create_all` creates tables that do not exist yet, but it never changes a table that
already exists (for example adding a column to `executions` in a hub.db created by an older Hub).
Those changes are migrations: numbered steps, applied once each and recorded in `schema_version`.

Rules for writing a migration:
- Append to MIGRATIONS with the next number; never renumber or edit a released migration.
- Make each step safe to run on a database that already has the change (use the helpers below),
  because a new database gets every table and column from create_all before the migrations run.
- Keep the SQL portable between SQLite and PostgreSQL where possible.
No third-party migration tool is used, so the Hub has no extra dependency.
"""
import logging
import weakref
from datetime import datetime, timezone
from typing import Callable, List, NamedTuple

from sqlalchemy import event, inspect, text
from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger("kinenix.hub")

_transactional_engines: "weakref.WeakSet[Engine]" = weakref.WeakSet()


def make_sqlite_transactional(engine: Engine) -> None:
    """
    Python's sqlite3 module commits ALTER TABLE and other DDL at once, outside the transaction, so a
    migration that fails halfway would leave half its changes behind. SQLAlchemy's documented fix:
    let SQLAlchemy emit BEGIN itself. Safe to call more than once.
    """
    if engine.dialect.name != "sqlite" or engine in _transactional_engines:
        return

    @event.listens_for(engine, "connect")
    def _no_driver_transactions(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _begin(conn):
        conn.exec_driver_sql("BEGIN")

    _transactional_engines.add(engine)
    engine.dispose()  # pooled connections were opened before the listeners existed


class Migration(NamedTuple):
    number: int
    name: str
    apply: Callable[[Connection], None]


def add_column_if_missing(conn: Connection, table: str, column: str, ddl_type: str) -> None:
    """ALTER TABLE ... ADD COLUMN, skipped when the column exists (for example from create_all)."""
    existing = {c["name"] for c in inspect(conn).get_columns(table)}
    if column not in existing:
        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {ddl_type}'))


def create_index_if_missing(conn: Connection, name: str, table: str, columns: str) -> None:
    conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})"))


def _baseline(conn: Connection) -> None:
    """The schema of Hub 0.2.0b3 (workers, executions); create_all has already made it."""


MIGRATIONS: List[Migration] = [
    Migration(1, "baseline: workers and executions", _baseline),
]


def _ensure_version_table(conn: Connection) -> None:
    conn.execute(text(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        " version INTEGER PRIMARY KEY,"
        " name VARCHAR(200) NOT NULL,"
        " applied_at VARCHAR(40) NOT NULL)"
    ))


def applied_versions(engine: Engine) -> List[int]:
    with engine.connect() as conn:
        if not inspect(conn).has_table("schema_version"):
            return []
        return [row[0] for row in conn.execute(text("SELECT version FROM schema_version ORDER BY version"))]


def current_version(engine: Engine) -> int:
    versions = applied_versions(engine)
    return versions[-1] if versions else 0


def run_migrations(engine: Engine, migrations: List[Migration] = MIGRATIONS) -> List[int]:
    """Applies the migrations not recorded yet, each in its own transaction. Returns the numbers applied."""
    make_sqlite_transactional(engine)
    with engine.begin() as conn:
        _ensure_version_table(conn)
    done = set(applied_versions(engine))
    applied: List[int] = []
    for migration in sorted(migrations, key=lambda m: m.number):
        if migration.number in done:
            continue
        # One transaction per migration: a failing step leaves the database as it was before that step
        with engine.begin() as conn:
            migration.apply(conn)
            conn.execute(
                text("INSERT INTO schema_version (version, name, applied_at) VALUES (:v, :n, :t)"),
                {"v": migration.number, "n": migration.name,
                 "t": datetime.now(timezone.utc).isoformat(timespec="seconds")},
            )
        applied.append(migration.number)
        logger.info(f"Database migration {migration.number} applied: {migration.name}")
    return applied

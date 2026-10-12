from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL lets workers write while dashboards, `kinenix hub` commands, and AI tools read.
        # An in-memory database has no journal file and stays in its own mode.
        cursor.execute("PRAGMA journal_mode=WAL")
        # Wait for a lock instead of failing at once with "database is locked"
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    from .migrations import make_sqlite_transactional
    make_sqlite_transactional(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create missing tables, then apply schema migrations to an existing database (see migrations.py)."""
    from . import models  # noqa: F401  (registers every table on Base)
    from .migrations import run_migrations

    Base.metadata.create_all(bind=engine)
    run_migrations(engine)

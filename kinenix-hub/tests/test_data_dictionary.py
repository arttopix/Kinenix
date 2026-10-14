"""docs/hub_data.md documents every table, view, column, and details key of the Hub database, and nothing else."""
import re
from pathlib import Path
from typing import Dict, Set

from sqlalchemy import create_engine, inspect

from kinenix_hub import models  # noqa: F401  (registers the tables on Base)
from kinenix_hub.database import Base
from kinenix_hub.migrations import run_migrations
from kinenix_hub.services.run_records import EXECUTION_DETAILS_KEYS, FAILURE_DETAILS_KEYS, STEP_DETAILS_KEYS
from kinenix_hub.views import create_views

DICTIONARY = Path(__file__).resolve().parents[2] / "docs" / "hub_data.md"


def _documented() -> Dict[str, Set[str]]:
    """{`name` or `table.details`: the names in the first column of the table under its heading}."""
    documented: Dict[str, Set[str]] = {}
    current = None
    for line in DICTIONARY.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^#{3,4} `([\w.]+)`$", line)
        if heading:
            current = heading.group(1)
            documented[current] = set()
        elif line.startswith("## "):
            current = None
        elif current:
            row = re.match(r"^\| `(\w+)` \|", line)
            if row:
                documented[current].add(row.group(1))
    return documented


def _database(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'hub.db').as_posix()}")
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    create_views(engine)
    return engine


def test_every_table_view_and_column_is_documented(tmp_path):
    inspector = inspect(_database(tmp_path))
    actual = {name: {c["name"] for c in inspector.get_columns(name)}
              for name in inspector.get_table_names() + inspector.get_view_names()}
    documented = {name: cols for name, cols in _documented().items() if "." not in name}
    assert set(documented) == set(actual)
    for name, columns in actual.items():
        assert documented[name] == columns, (
            f"{name}: not documented {sorted(columns - documented[name])}, "
            f"documented but missing {sorted(documented[name] - columns)}")


def test_every_details_key_is_documented():
    documented = _documented()
    for table, keys in (("executions", EXECUTION_DETAILS_KEYS), ("step_results", STEP_DETAILS_KEYS),
                        ("failures", FAILURE_DETAILS_KEYS)):
        assert documented[f"{table}.details"] == set(keys), table

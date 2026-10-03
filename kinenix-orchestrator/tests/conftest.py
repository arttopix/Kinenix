import os
import tempfile
from pathlib import Path

# Keep tests away from the developer's real data. Both must be set before any test module
# imports kinenix_orchestrator, because config and database read them at import time.
_test_dir = Path(tempfile.mkdtemp(prefix="kinenix-orchestrator-tests-"))

# Saved settings from `kinenix orchestrator setup` (~/.kinenix/orchestrator.env) must not change test behavior
os.environ["ORCHESTRATOR_SETTINGS_FILE"] = str(_test_dir / "no-settings.env")

# Test workers and executions go to a throwaway database, not the default orchestrator.db
os.environ["DATABASE_URL"] = f"sqlite:///{(_test_dir / 'test.db').as_posix()}"

import os
import tempfile
from pathlib import Path

# Keep tests independent of the developer's saved ~/.kinenix/orchestrator.env.
# Set before any test module imports kinenix_orchestrator.config.
os.environ["ORCHESTRATOR_SETTINGS_FILE"] = str(Path(tempfile.gettempdir()) / "kinenix-tests-no-settings.env")

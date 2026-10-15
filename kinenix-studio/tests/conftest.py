import os
import tempfile
from pathlib import Path

# Keep tests away from ~/.kinenix/kinenix.env: a Hub saved there by `kinenix connect` would receive every
# test run. Set before any test imports kinenix; subprocesses started by tests inherit it.
os.environ["KINENIX_SETTINGS_FILE"] = str(Path(tempfile.mkdtemp(prefix="kinenix-tests-")) / "kinenix.env")

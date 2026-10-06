"""Repository-wide rules from AGENTS.md that can be checked automatically."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Emoji and pictograph ranges, plus the variation selector that turns symbols into emoji
EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".xlsx", ".db", ".pdf", ".woff", ".woff2")


def _tracked_text_files():
    if not shutil.which("git"):
        pytest.skip("git is not available")
    result = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("not a git checkout")
    for name in result.stdout.splitlines():
        if name.endswith(SKIP_SUFFIXES) or "package-lock" in name:
            continue
        path = REPO_ROOT / name
        try:
            yield name, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue


def _version_of(init_file: str) -> str:
    text = (REPO_ROOT / init_file).read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', text).group(1)


def test_published_packages_share_one_version():
    """kinenix, kinenix-hub, and kinenix-worker are released together (docs/releasing.md)."""
    versions = {
        "kinenix": _version_of("kinenix-core/kinenix/__init__.py"),
        "kinenix-hub": _version_of("kinenix-hub/kinenix_hub/__init__.py"),
        "kinenix-worker": _version_of("kinenix-worker/kinenix_worker/__init__.py"),
    }
    assert len(set(versions.values())) == 1, f"bump all packages together: {versions}"
    version = versions["kinenix"]

    core = (REPO_ROOT / "kinenix-core/pyproject.toml").read_text(encoding="utf-8")
    hub = (REPO_ROOT / "kinenix-hub/pyproject.toml").read_text(encoding="utf-8")
    worker = (REPO_ROOT / "kinenix-worker/pyproject.toml").read_text(encoding="utf-8")
    # Each package needs its siblings at the same release, so a mixed install cannot happen
    assert f'"kinenix-hub>={version}"' in core
    assert f'"kinenix-worker>={version}"' in core
    assert f'"kinenix>={version}"' in hub
    assert f'"kinenix>={version}"' in worker


def test_no_emojis_in_repository():
    """AGENTS.md rule 6: no emojis in code, comments, UI text, or documentation."""
    found = [
        f"{name}:{line_no}: {''.join(EMOJI.findall(line))}"
        for name, text in _tracked_text_files()
        for line_no, line in enumerate(text.splitlines(), 1)
        if EMOJI.search(line)
    ]
    assert found == [], "Remove emojis: " + "; ".join(found[:20])

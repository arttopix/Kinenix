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


def test_no_emojis_in_repository():
    """AGENTS.md rule 6: no emojis in code, comments, UI text, or documentation."""
    found = [
        f"{name}:{line_no}: {''.join(EMOJI.findall(line))}"
        for name, text in _tracked_text_files()
        for line_no, line in enumerate(text.splitlines(), 1)
        if EMOJI.search(line)
    ]
    assert found == [], "Remove emojis: " + "; ".join(found[:20])

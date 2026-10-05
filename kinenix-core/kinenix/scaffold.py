"""`kinenix init`: create a new flow project from an example bundle shipped inside the package.

The examples in kinenix/examples/ are copies of flows/examples/ in the repository, kept in sync by
.github/scripts/sync_examples.py (a test fails when they differ).
"""
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple

from .engine.markdown import markdown_to_flow, sync_flow_json
from .models.flow import Step

EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"
DEFAULT_EXAMPLE = "hello"


def _walk(steps: Iterable[Step]) -> Iterable[Step]:
    for step in steps or []:
        yield step
        yield from _walk(step.sub_steps)
        yield from _walk(step.else_steps)


def available_examples() -> List[Tuple[str, str, bool]]:
    """(name, description, needs_browser) for each packaged example, the default first."""
    found = []
    for folder in sorted(p for p in EXAMPLES_DIR.iterdir() if (p / "flow.md").is_file()):
        flow = markdown_to_flow((folder / "flow.md").read_text(encoding="utf-8-sig"))
        needs_browser = any(step.action.startswith("web.") for step in _walk(flow.steps))
        found.append((folder.name, flow.description or flow.name, needs_browser))
    return sorted(found, key=lambda item: (item[0] != DEFAULT_EXAMPLE, item[0]))


def create_project(target: Path, example: str = DEFAULT_EXAMPLE) -> Path:
    """Copy an example into `target` (which must not exist or be empty) and make sure flow.json is built.

    Raises ValueError for an unknown example and FileExistsError when `target` already has files.
    """
    source = EXAMPLES_DIR / example
    if not (source / "flow.md").is_file():
        names = ", ".join(name for name, _, _ in available_examples())
        raise ValueError(f"Unknown example '{example}'. Available: {names}")

    target = Path(target).resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError(f"{target} already exists and is not empty; choose another folder.")

    shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    sync_flow_json(target / "flow.md")
    return target

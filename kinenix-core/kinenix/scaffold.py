"""`kinenix init`: create a flow project.

- `kinenix init "Get stock data"` creates a new project for a task from templates/new_project: a requirements
  file to describe the task, instructions for AI assistants, a flow.md skeleton, config, and .env.example.
- `kinenix init --example NAME` copies a complete example bundle from examples/. Those are copies of
  flows/examples/ in the repository, kept in sync by .github/scripts/sync_examples.py (a test fails when they differ).
"""
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .engine.markdown import markdown_to_flow, sync_flow_json
from .models.flow import Step

PACKAGE_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = PACKAGE_DIR / "examples"
NEW_PROJECT_TEMPLATE = PACKAGE_DIR / "templates" / "new_project"
DEFAULT_EXAMPLE = "hello"

# Packaged under names without a leading dot, because package data globs skip dotfiles
DOTFILE_NAMES = {"gitignore": ".gitignore", "env.example": ".env.example"}
TEXT_SUFFIXES = {".md", ".json", ".txt", ".example", ""}


def project_folder_name(title: str) -> str:
    """'Get stock data' -> 'get_stock_data'. Letters of any script are kept, so Thai titles work too.

    Combining marks (category M, such as Thai vowels and tone marks) are kept with their letters;
    a plain \\w pattern would split 'ดึง' into 'ด_ง'.
    """
    kept = "".join(c if unicodedata.category(c)[0] in "LMN" else " " for c in title.strip().lower())
    slug = re.sub(r"\s+", "_", kept.strip())
    if not slug:
        raise ValueError(f"Cannot make a folder name from '{title}'; use letters or digits.")
    return slug


def _check_target(target: Path) -> Path:
    target = Path(target).resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError(f"{target} already exists and is not empty; choose another name or folder.")
    return target


def create_new_project(title: str, target: Optional[Path] = None) -> Path:
    """Create a project for a new task: requirements.md, AGENTS.md, flow.md skeleton, config, and .env.example."""
    title = title.strip()
    target = _check_target(Path(target) if target else Path(project_folder_name(title)))
    for source in sorted(NEW_PROJECT_TEMPLATE.rglob("*")):
        if not source.is_file() or "__pycache__" in source.parts:
            continue
        rel = source.relative_to(NEW_PROJECT_TEMPLATE)
        dest = target / rel.parent / DOTFILE_NAMES.get(rel.name, rel.name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or rel.name in DOTFILE_NAMES:
            dest.write_text(source.read_text(encoding="utf-8").replace("{{title}}", title), encoding="utf-8")
        else:
            dest.write_bytes(source.read_bytes())
    sync_flow_json(target / "flow.md")
    return target


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

    target = _check_target(target)
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    sync_flow_json(target / "flow.md")
    return target

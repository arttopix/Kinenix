"""The data dictionary (docs/hub_data.md) as data, for `kinenix hub query --list` and `--describe`.

The package holds a copy of docs/hub_data.md (hub_data.md next to this file), because pip installs only
what is inside the package; a test fails when the two differ.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

DICTIONARY_FILE = Path(__file__).resolve().parent / "hub_data.md"


@dataclass
class Entry:
    """One table, view, or `details` column: what it answers, and each column's meaning and example."""
    name: str
    description: str = ""
    columns: Dict[str, Tuple[str, str]] = field(default_factory=dict)


def _plain(text: str) -> str:
    """Markdown links and code marks removed, for the terminal."""
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).replace("`", "").strip()


def _cell(text: str) -> str:
    text = text.strip()
    if text.count("`") == 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]  # an example value, kept as written
    return _plain(text)


def parse(text: str) -> Dict[str, Entry]:
    """Entries under `### \\`name\\`` (tables and views) and `#### \\`name.details\\`` headings."""
    entries: Dict[str, Entry] = {}
    current: Optional[Entry] = None
    for line in text.splitlines():
        heading = re.match(r"^#{3,4} `([\w.]+)`$", line)
        if heading:
            current = Entry(heading.group(1))
            entries[current.name] = current
        elif line.startswith("## "):
            current = None
        elif current is not None:
            row = re.match(r"^\| `(\w+)` \|(.*)\|\s*$", line)
            if row:
                cells = row.group(2).split(" | ")
                meaning = _cell(cells[0]) if cells else ""
                example = _cell(cells[1]) if len(cells) > 1 else ""
                current.columns[row.group(1)] = (meaning, example)
            elif line.strip() and not line.startswith("|") and not current.columns:
                current.description = f"{current.description} {_plain(line)}".strip()
    return entries


def load(path: Path = DICTIONARY_FILE) -> Dict[str, Entry]:
    return parse(path.read_text(encoding="utf-8")) if path.is_file() else {}

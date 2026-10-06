"""Copy the example bundles that `kinenix init` offers into the kinenix package.

Usage:
    python .github/scripts/sync_examples.py           copy flows/examples/* into kinenix-core/kinenix/examples/
    python .github/scripts/sync_examples.py --check   report differences without writing (exit 1 when out of date)

flows/examples/ is the source. The package holds a copy because pip installs only what is inside the package.
Per example, the copy contains flow.md, flow.json, README.md, the config template as config/config.json, and
input data in assets/ (screenshots and other outputs are left out).
"""
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "flows" / "examples"
TARGET = REPO_ROOT / "kinenix-core" / "kinenix" / "examples"
EXAMPLES = ("hello", "bot_fx_rate", "rpachallenge")
ASSET_SUFFIXES = (".xlsx", ".xls", ".csv", ".txt", ".pdf")


def expected_files(name: str) -> Dict[str, Path]:
    """Packaged relative path -> source file, for one example."""
    src = SOURCE / name
    files = {
        "flow.md": src / "flow.md",
        "flow.json": src / "flow.json",
        "README.md": src / "README.md",
        "config/config.json": src / "config" / "config.template.json",
    }
    assets = src / "assets"
    if assets.is_dir():
        for path in sorted(assets.iterdir()):
            if path.is_file() and path.suffix.lower() in ASSET_SUFFIXES:
                files[f"assets/{path.name}"] = path
    return files


def problems() -> List[str]:
    found = []
    for name in EXAMPLES:
        expected = expected_files(name)
        for rel, source in expected.items():
            if not source.is_file():
                found.append(f"{name}: source {source.relative_to(REPO_ROOT)} is missing")
                continue
            copy = TARGET / name / rel
            if not copy.is_file():
                found.append(f"{name}: {rel} is not in the package")
            elif copy.read_bytes() != source.read_bytes():
                found.append(f"{name}: {rel} differs from {source.relative_to(REPO_ROOT)}")
        extra_dir = TARGET / name
        if extra_dir.is_dir():
            for path in extra_dir.rglob("*"):
                rel = path.relative_to(extra_dir).as_posix()
                if path.is_file() and rel not in expected:
                    found.append(f"{name}: {rel} is in the package but not in the example")
    if TARGET.is_dir():
        for path in TARGET.iterdir():
            if path.is_dir() and path.name not in EXAMPLES and path.name != "__pycache__":
                found.append(f"{path.name}: packaged but not listed in EXAMPLES")
    return found


def sync() -> None:
    for name in EXAMPLES:
        target_dir = TARGET / name
        expected = expected_files(name)
        if target_dir.is_dir():
            for path in sorted(target_dir.rglob("*"), reverse=True):
                rel = path.relative_to(target_dir).as_posix()
                if path.is_file() and rel not in expected:
                    path.unlink()
        for rel, source in expected.items():
            copy = target_dir / rel
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(source.read_bytes())
        print(f"synced {name}: {len(expected)} files")


if __name__ == "__main__":
    if "--check" in sys.argv:
        issues = problems()
        for issue in issues:
            print("OUT OF DATE:", issue)
        if issues:
            print("Run: python .github/scripts/sync_examples.py")
        sys.exit(1 if issues else 0)
    sync()

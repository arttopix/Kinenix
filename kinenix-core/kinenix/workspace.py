"""Where the user's own flows live: the flows folder.

Flows are kept apart from the Kinenix source code, by default in ~/kinenix-flows on every system
(C:\\Users\\<name>\\kinenix-flows on Windows, /home/<name>/kinenix-flows on Linux). It is not hidden, so flows
are easy to open and review, and on Windows it is outside Documents, which OneDrive often syncs to the cloud.

The location comes from, in order: the KINENIX_FLOWS_DIR environment variable, the saved setting in
~/.kinenix/kinenix.env (written the first time `kinenix init` asks, or by `kinenix flows-dir PATH`), and
the default. ~/.kinenix itself keeps settings and data (hub.env, hub.db, worker.env), not flows.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, Optional

ENV_VAR = "KINENIX_FLOWS_DIR"
SETTING_KEY = "KINENIX_FLOWS_DIR"


def default_flows_dir() -> Path:
    return Path.home() / "kinenix-flows"


def settings_file() -> Path:
    return Path.home() / ".kinenix" / "kinenix.env"


def _read_settings(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def configured_flows_dir() -> Optional[Path]:
    """The flows folder chosen by the user (environment or saved setting), or None if never chosen."""
    value = os.environ.get(ENV_VAR) or _read_settings(settings_file()).get(SETTING_KEY)
    return Path(value).expanduser() if value else None


def flows_dir() -> Path:
    return configured_flows_dir() or default_flows_dir()


def save_flows_dir(path: Path) -> Path:
    """Remember the flows folder in ~/.kinenix/kinenix.env, keeping any other settings in that file."""
    path = Path(path).expanduser().resolve()
    target = settings_file()
    values = _read_settings(target)
    values[SETTING_KEY] = str(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Kinenix settings. The KINENIX_FLOWS_DIR environment variable takes precedence."]
    lines += [f"{key}={value}" for key, value in values.items()]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


FLOWS_GITIGNORE = """# Kinenix flows: results, logs, and secrets stay on this machine
output/
logs/
.env
__pycache__/
"""

FLOWS_README = """# Kinenix flows

Automation flows built with [Kinenix](https://github.com/arttopix/Kinenix), one folder per task.

- New task: `kinenix init "Task name"` creates a folder here with requirements.md and instructions for an AI assistant.
- Run one from anywhere: `kinenix run <folder name>`.
- Keep this repository **private**: flows and their requirements often describe internal systems and business data.
"""


def prepare_flows_dir(path: Path, use_git: bool) -> Path:
    """Create the flows folder; with use_git, also a git repository with a .gitignore and README if new."""
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    if not (path / ".gitignore").exists():
        (path / ".gitignore").write_text(FLOWS_GITIGNORE, encoding="utf-8")
    if not (path / "README.md").exists():
        (path / "README.md").write_text(FLOWS_README, encoding="utf-8")
    if use_git and not (path / ".git").exists() and shutil.which("git"):
        subprocess.run(["git", "init", "-q", str(path)], check=False)
    return path


def ensure_flows_dir(interactive: bool, ask: Callable[[str], str] = input,
                     say: Callable[[str], None] = print) -> Path:
    """Return the flows folder, creating it. Asks where to put it the first time, when someone is at the terminal.

    Without a terminal (scripts, CI, services) the default is used and nothing is saved, so the question
    is still asked the first time a person runs `kinenix init`.
    """
    chosen = configured_flows_dir()
    if chosen is not None:
        return prepare_flows_dir(chosen, use_git=False)
    if not interactive:
        return prepare_flows_dir(default_flows_dir(), use_git=False)

    default = default_flows_dir()
    say("Kinenix keeps your flows in one folder, separate from the Kinenix source code.")
    answer = ask(f"Where should your flows live? [{default}]: ").strip()
    path = Path(answer).expanduser() if answer else default
    use_git = ask("Create a git repository there for version history? [Y/n]: ").strip().lower() not in ("n", "no")
    path = prepare_flows_dir(path, use_git)
    save_flows_dir(path)
    say(f"Flows folder: {path}  (saved in {settings_file()}; change it with: kinenix flows-dir PATH)\n")
    return path

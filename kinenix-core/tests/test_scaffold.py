"""`kinenix init` and the example bundles shipped in the package."""
import csv
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from kinenix import scaffold
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.logger import ExecutionLogger
from kinenix.engine.markdown import load_flow
from kinenix.engine.validation import validate_flow

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_examples_are_listed_with_the_default_first():
    examples = scaffold.available_examples()
    names = [name for name, _, _ in examples]
    assert names[0] == scaffold.DEFAULT_EXAMPLE == "hello"
    assert {"hello", "bot_fx_rate", "rpachallenge"} <= set(names)
    needs_browser = {name: nb for name, _, nb in examples}
    assert needs_browser["hello"] is False
    assert needs_browser["bot_fx_rate"] is True and needs_browser["rpachallenge"] is True
    assert all(description for _, description, _ in examples)


def test_hello_project_is_created_and_runs(tmp_path):
    project = scaffold.create_project(tmp_path / "my-bot")
    assert sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file()) == [
        "README.md", "config/config.json", "flow.json", "flow.md",
    ]

    flow = load_flow(project / "flow.json")
    ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
        flow, initial_vars={"__flow_dir__": str(project)}
    )
    assert not ctx.has_error
    with open(project / "output" / "greetings.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0] == {"Name": "Somchai", "Greeting": "Hello, Somchai!"}
    assert len(rows) == 3


def test_empty_names_stop_with_a_business_error(tmp_path):
    project = scaffold.create_project(tmp_path / "empty")
    (project / "config" / "config.json").write_text('{"names": [], "greeting": "Hi", "output_path": "./out.csv"}',
                                                    encoding="utf-8")
    ctx = FlowInterpreter(logger=ExecutionLogger(log_dir=tmp_path / "logs")).run_flow(
        load_flow(project / "flow.json"), initial_vars={"__flow_dir__": str(project)}
    )
    assert ctx.has_error
    assert ctx.failure_details.error_type == "Business"
    assert not (project / "out.csv").exists()


def test_existing_folder_rules(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert scaffold.create_project(empty, "bot_fx_rate") == empty.resolve()  # an empty folder is fine

    used = tmp_path / "used"
    used.mkdir()
    (used / "notes.txt").write_text("keep me", encoding="utf-8")
    with pytest.raises(FileExistsError):
        scaffold.create_project(used)
    assert (used / "notes.txt").read_text(encoding="utf-8") == "keep me"

    with pytest.raises(ValueError, match="Available: hello"):
        scaffold.create_project(tmp_path / "x", "nope")


def test_every_example_creates_a_valid_project(tmp_path):
    for name, _, _ in scaffold.available_examples():
        project = scaffold.create_project(tmp_path / name, name)
        assert validate_flow(load_flow(project / "flow.md")) == [], name
        assert (project / "flow.json").is_file()
    assert (tmp_path / "rpachallenge" / "assets" / "challenge.xlsx").is_file()
    assert not list((tmp_path / "rpachallenge" / "assets").glob("*.png"))  # outputs are not shipped


def test_packaged_examples_match_flows_examples():
    """The package copies must equal flows/examples (run .github/scripts/sync_examples.py after editing)."""
    sync = runpy.run_path(str(REPO_ROOT / ".github" / "scripts" / "sync_examples.py"))
    assert sync["problems"]() == []


def test_packaged_example_files_are_not_git_ignored():
    """A file that exists locally but is ignored by git would pass locally and be missing from CI and the wheel."""
    import shutil
    if not shutil.which("git"):
        pytest.skip("git is not available")
    files = [str(p.relative_to(REPO_ROOT)) for p in scaffold.EXAMPLES_DIR.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts]
    result = subprocess.run(["git", "check-ignore", "--no-index", *files], cwd=REPO_ROOT,
                            capture_output=True, text=True)
    assert result.stdout.strip() == "", f"Ignored by .gitignore: {result.stdout.split()}"


def test_packaged_examples_are_not_discovered_as_runnable_flows():
    from kinenix.cli import discover_flows

    for path, _ in discover_flows().values():
        assert scaffold.EXAMPLES_DIR not in path.resolve().parents


def test_init_command(tmp_path):
    def kinenix(*args):
        return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=tmp_path,
                              capture_output=True, text=True, timeout=120)

    listing = kinenix("init", "--list")
    assert listing.returncode == 0 and "hello" in listing.stdout and "needs a browser" in listing.stdout

    created = kinenix("init", "fx", "--example", "bot_fx_rate")
    assert created.returncode == 0
    assert "kinenix install-browsers" in created.stdout and "kinenix run fx" in created.stdout
    assert (tmp_path / "fx" / "flow.md").is_file()

    again = kinenix("init", "fx")
    assert again.returncode == 1 and "not empty" in again.stderr

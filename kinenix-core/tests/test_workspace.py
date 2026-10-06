"""The flows folder: where `kinenix init` puts projects and where `kinenix run NAME` finds them."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kinenix import workspace


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A fake home folder, so tests never touch ~/kinenix-flows or ~/.kinenix."""
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake))
    monkeypatch.delenv("KINENIX_FLOWS_DIR", raising=False)
    return fake


def test_default_is_kinenix_flows_in_home(home):
    assert workspace.configured_flows_dir() is None
    assert workspace.flows_dir() == home / "kinenix-flows"


def test_environment_beats_saved_setting(home, monkeypatch, tmp_path):
    workspace.save_flows_dir(tmp_path / "saved")
    assert workspace.flows_dir() == (tmp_path / "saved").resolve()
    assert "KINENIX_FLOWS_DIR=" in workspace.settings_file().read_text(encoding="utf-8")

    monkeypatch.setenv("KINENIX_FLOWS_DIR", str(tmp_path / "from-env"))
    assert workspace.flows_dir() == tmp_path / "from-env"


def test_first_interactive_run_asks_and_remembers(home, tmp_path):
    answers = iter([str(tmp_path / "my-flows"), "y"])
    said = []
    path = workspace.ensure_flows_dir(interactive=True, ask=lambda _: next(answers), say=said.append)
    assert path == (tmp_path / "my-flows").resolve()
    assert (path / ".gitignore").read_text(encoding="utf-8").count(".env") == 1
    assert "private" in (path / "README.md").read_text(encoding="utf-8")
    if subprocess.run(["git", "--version"], capture_output=True).returncode == 0:
        assert (path / ".git").is_dir()

    # Saved: the second run asks nothing
    again = workspace.ensure_flows_dir(interactive=True, ask=lambda _: pytest.fail("asked twice"), say=said.append)
    assert again == path


def test_enter_accepts_the_default_and_no_skips_git(home):
    answers = iter(["", "n"])
    path = workspace.ensure_flows_dir(interactive=True, ask=lambda _: next(answers), say=lambda _: None)
    assert path == (home / "kinenix-flows").resolve()
    assert not (path / ".git").exists()


def test_without_a_terminal_the_default_is_used_and_not_saved(home):
    path = workspace.ensure_flows_dir(interactive=False, ask=lambda _: pytest.fail("asked in a script"))
    assert path == (home / "kinenix-flows").resolve()
    assert not workspace.settings_file().exists()


def test_saving_keeps_other_settings(home, tmp_path):
    target = workspace.settings_file()
    target.parent.mkdir(parents=True)
    target.write_text("OTHER=1\n", encoding="utf-8")
    workspace.save_flows_dir(tmp_path / "f")
    text = target.read_text(encoding="utf-8")
    assert "OTHER=1" in text and "KINENIX_FLOWS_DIR=" in text


def _cli(tmp_path, *args, cwd=None):
    env = {**os.environ, "KINENIX_FLOWS_DIR": str(tmp_path / "flows")}
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=cwd or tmp_path, env=env,
                          capture_output=True, text=True, timeout=120)


def test_init_puts_projects_in_the_flows_folder_and_run_finds_them_by_name(tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    created = _cli(tmp_path, "init", "Get stock data", cwd=elsewhere)
    assert created.returncode == 0, created.stderr
    assert (tmp_path / "flows" / "get_stock_data" / "requirements.md").is_file()
    assert not (elsewhere / "get_stock_data").exists()
    assert "kinenix run get_stock_data" in created.stdout

    assert _cli(tmp_path, "init", "demo", "--example", "hello", cwd=elsewhere).returncode == 0
    run = _cli(tmp_path, "run", "demo", cwd=elsewhere)  # by name, from another folder
    assert run.returncode == 0, run.stderr
    assert (tmp_path / "flows" / "demo" / "output" / "greetings.csv").is_file()

    listed = _cli(tmp_path, "list", cwd=elsewhere)
    assert "get_stock_data" in listed.stdout and "demo" in listed.stdout


def test_init_dir_overrides_the_flows_folder(tmp_path):
    result = _cli(tmp_path, "init", "Report", "--dir", str(tmp_path / "custom"))
    assert result.returncode == 0
    assert (tmp_path / "custom" / "requirements.md").is_file()
    assert str(tmp_path / "custom") in result.stdout  # outside the flows folder, run it by path


def test_flows_dir_command(tmp_path):
    shown = _cli(tmp_path, "flows-dir")
    assert shown.returncode == 0 and str(tmp_path / "flows") in shown.stdout and "KINENIX_FLOWS_DIR" in shown.stdout

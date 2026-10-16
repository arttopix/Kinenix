"""flow.md is the only flow file: no flow.json is written or read, and old JSON flows explain how to convert."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import load_flow, markdown_issues, markdown_to_flow

REPO_ROOT = Path(__file__).resolve().parents[2]

HELLO = """# Hello

## Steps

### 1. Say Hello (`file.write_text`)
- **path:** ./output/hello.txt
- **content:** hello
"""

OLD_JSON = {"name": "Old Flow", "steps": [
    {"id": "step_1", "name": "Count", "action": "logic.set_variable", "parameters": {"name": "count", "value": "100"}},
    {"id": "step_2", "name": "Write", "action": "file.write_text",
     "parameters": {"path": "./output/count.txt", "content": "${count}"}}]}


def cli(cwd, *args):
    env = {**os.environ, "KINENIX_FLOWS_DIR": str(cwd / "no-flows-folder")}
    return subprocess.run([sys.executable, "-m", "kinenix.cli", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=120)


def test_run_reads_flow_md_and_writes_no_flow_json(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "flow.md").write_text(HELLO, encoding="utf-8")
    result = cli(tmp_path, "run", str(bundle))
    assert result.returncode == 0, result.stderr
    assert (bundle / "output" / "hello.txt").read_text(encoding="utf-8") == "hello"
    assert not (bundle / "flow.json").exists()
    assert "flow.json" not in result.stdout + result.stderr


def test_a_json_flow_is_not_run_and_says_how_to_convert(tmp_path):
    bundle = tmp_path / "old"
    bundle.mkdir()
    (bundle / "flow.json").write_text(json.dumps(OLD_JSON), encoding="utf-8")
    with pytest.raises(ValueError, match="kinenix export-md"):
        load_flow(bundle)
    result = cli(tmp_path, "run", str(bundle))
    assert result.returncode == 1 and "kinenix export-md" in result.stderr


def test_export_md_converts_an_old_flow_once_and_keeps_value_types(tmp_path):
    bundle = tmp_path / "old"
    bundle.mkdir()
    (bundle / "flow.json").write_text(json.dumps(OLD_JSON), encoding="utf-8")
    assert cli(tmp_path, "export-md", str(bundle)).returncode == 0
    md = (bundle / "flow.md").read_text(encoding="utf-8")
    assert '- **value:** "100"' in md  # the text "100" stays text
    assert markdown_to_flow(md).steps[0].parameters["value"] == "100"
    result = cli(tmp_path, "run", str(bundle))
    assert result.returncode == 0, result.stderr
    assert (bundle / "output" / "count.txt").read_text(encoding="utf-8") == "100"


def test_compile_prints_json_and_writes_only_where_asked(tmp_path):
    (tmp_path / "flow.md").write_text(HELLO, encoding="utf-8")
    printed = cli(tmp_path, "compile", "flow.md")
    assert printed.returncode == 0, printed.stderr
    assert json.loads(printed.stdout)["steps"][0]["action"] == "file.write_text"
    assert not (tmp_path / "flow.json").exists()

    assert cli(tmp_path, "compile", "flow.md", "-o", "inspect/compiled.json").returncode == 0
    assert json.loads((tmp_path / "inspect" / "compiled.json").read_text(encoding="utf-8"))["name"] == "Hello"
    assert not (tmp_path / "flow.json").exists()


def test_a_json_subflow_is_not_run(tmp_path):
    (tmp_path / "child.json").write_text(json.dumps(OLD_JSON), encoding="utf-8")
    flow = markdown_to_flow("# P\n\n## Steps\n\n### 1. Call (`flow.call`)\n- **flow:** ./child.json\n")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(tmp_path)})
    assert ctx.has_error and "kinenix export-md" in ctx.failure_details.error_message


def test_step_heading_without_an_action_is_reported(tmp_path):
    markdown = "# T\n\n## Steps\n\n### 1. Open The Page\n- **url:** https://example.com\n\n" \
               "### 2. Close (`web.close`)\n"
    flow = markdown_to_flow(markdown)
    assert [s.name for s in flow.steps] == ["Close"]
    issues = markdown_issues(markdown)
    assert len(issues) == 1 and "Line 5" in issues[0] and "has no action" in issues[0]


def test_a_flow_without_steps_is_reported_and_not_run(tmp_path):
    markdown = "# Empty\n\n## Steps\n\n### 1. Open The Page\n- **web.open**\n"
    assert any("No steps found" in issue for issue in markdown_issues(markdown))
    bundle = tmp_path / "empty"
    bundle.mkdir()
    (bundle / "flow.md").write_text(markdown, encoding="utf-8")
    assert cli(tmp_path, "validate", str(bundle)).returncode == 1
    result = cli(tmp_path, "run", str(bundle))
    assert result.returncode == 1 and "has no steps" in result.stderr


def test_no_flow_json_in_the_repository():
    tracked = subprocess.run(["git", "ls-files", "*flow.json", "flows/**/*.json"], cwd=REPO_ROOT,
                             capture_output=True, text=True).stdout.split()
    flows = [path for path in tracked if "/config/" not in path]
    assert flows == [], "Flows are flow.md files; convert these with kinenix export-md"

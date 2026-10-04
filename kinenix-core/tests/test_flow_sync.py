import json
import os
from pathlib import Path

import pytest

from kinenix.engine.markdown import FlowSync, markdown_to_flow, sync_flow_json
from kinenix.models.flow import FlowDefinition

REPO_ROOT = Path(__file__).resolve().parents[2]

FLOW_MD = """# Sync Demo
> Description: Flow used by sync tests

### 1. Wait (`logic.wait`)
- seconds: 0
"""


def _bundle(tmp_path: Path) -> Path:
    md = tmp_path / "flow.md"
    md.write_text(FLOW_MD, encoding="utf-8")
    return md


def _set_mtime(path: Path, seconds_ago: int) -> None:
    stamp = path.stat().st_mtime - seconds_ago
    os.utime(path, (stamp, stamp))


def _json_name(md: Path) -> str:
    return json.loads(md.with_name("flow.json").read_text(encoding="utf-8"))["name"]


def test_missing_json_is_created(tmp_path):
    md = _bundle(tmp_path)
    assert sync_flow_json(md) == FlowSync.CREATED
    assert _json_name(md) == "Sync Demo"
    assert sync_flow_json(md) == FlowSync.UP_TO_DATE


def test_changed_markdown_is_recompiled(tmp_path):
    md = _bundle(tmp_path)
    sync_flow_json(md)
    _set_mtime(md.with_name("flow.json"), 60)
    md.write_text(FLOW_MD.replace("# Sync Demo", "# Sync Demo v2"), encoding="utf-8")
    assert sync_flow_json(md) == FlowSync.COMPILED
    assert _json_name(md) == "Sync Demo v2"


def test_json_edited_after_markdown_is_kept(tmp_path):
    md = _bundle(tmp_path)
    sync_flow_json(md)
    json_path = md.with_name("flow.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    data["name"] = "Edited in Studio"
    _set_mtime(md, 60)
    json_path.write_text(json.dumps(data), encoding="utf-8")
    assert sync_flow_json(md) == FlowSync.JSON_NEWER
    assert _json_name(md) == "Edited in Studio"


def test_formatting_only_difference_is_up_to_date(tmp_path):
    md = _bundle(tmp_path)
    sync_flow_json(md)
    json_path = md.with_name("flow.json")
    json_path.write_text(json.dumps(json.loads(json_path.read_text(encoding="utf-8"))), encoding="utf-8")
    _set_mtime(md, 60)
    assert sync_flow_json(md) == FlowSync.UP_TO_DATE


def test_invalid_json_is_rebuilt(tmp_path):
    md = _bundle(tmp_path)
    md.with_name("flow.json").write_text("{ not json", encoding="utf-8")
    _set_mtime(md, 60)
    assert sync_flow_json(md) == FlowSync.COMPILED
    assert _json_name(md) == "Sync Demo"


def test_files_with_utf8_bom_are_read(tmp_path):
    """Windows PowerShell 5 and some editors write a BOM; it must not hide the title or invalidate the JSON."""
    md = tmp_path / "flow.md"
    md.write_text(FLOW_MD, encoding="utf-8-sig")
    assert sync_flow_json(md) == FlowSync.CREATED
    assert _json_name(md) == "Sync Demo"

    json_path = md.with_name("flow.json")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    data["name"] = "Edited With BOM"
    _set_mtime(md, 60)
    json_path.write_text(json.dumps(data), encoding="utf-8-sig")
    assert sync_flow_json(md) == FlowSync.JSON_NEWER


def test_no_markdown(tmp_path):
    assert sync_flow_json(tmp_path / "flow.md") == FlowSync.NO_MARKDOWN


@pytest.mark.parametrize(
    "md_path",
    sorted((REPO_ROOT / "flows").rglob("flow.md")),
    ids=lambda p: str(p.parent.relative_to(REPO_ROOT)),
)
def test_committed_flow_json_matches_flow_md(md_path):
    """flow.json is a build artifact of flow.md; a mismatch means someone forgot `kinenix compile`."""
    json_path = md_path.with_name("flow.json")
    assert json_path.is_file(), f"Missing {json_path}; run: kinenix compile {md_path.parent}"
    compiled = markdown_to_flow(md_path.read_text(encoding="utf-8")).model_dump(exclude_none=True)
    committed = FlowDefinition.model_validate(json.loads(json_path.read_text(encoding="utf-8"))).model_dump(exclude_none=True)
    assert compiled == committed, f"{json_path} is out of date; run: kinenix compile {md_path.parent}"

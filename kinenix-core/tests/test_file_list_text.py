"""file.list, file.read_text, file.write_text, file.create_folder, and boolean parameters given as text."""
import json
import os
import time

import pytest

from kinenix.actions.registry import ActionRegistry
from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import markdown_to_flow
from kinenix.models.context import ExecutionContext


def run(action, flow_dir, **parameters):
    ctx = ExecutionContext(flow_name="t")
    ctx.set_variable("__flow_dir__", str(flow_dir))
    return ActionRegistry.get(action)().execute(parameters, ctx)


@pytest.fixture
def inbox(tmp_path):
    """inbox/ with b.csv (oldest, largest), a.csv, notes.txt (newest), and a subfolder with c.csv."""
    folder = tmp_path / "inbox"
    (folder / "archive").mkdir(parents=True)
    (folder / "b.csv").write_text("x" * 50, encoding="utf-8")
    (folder / "a.csv").write_text("x" * 10, encoding="utf-8")
    (folder / "notes.txt").write_text("hi", encoding="utf-8")
    (folder / "archive" / "c.csv").write_text("x", encoding="utf-8")
    now = time.time()
    for offset, name in enumerate(["b.csv", "a.csv", "notes.txt"]):
        os.utime(folder / name, (now - 300 + offset * 100, now - 300 + offset * 100))
    return tmp_path


def names(items):
    return [item["relative_path"] for item in items]


def test_list_files_by_pattern(inbox):
    items = run("file.list", inbox, path="./inbox", pattern="*.csv")
    assert names(items) == ["a.csv", "b.csv"]
    first = items[0]
    assert first["name"] == "a.csv" and first["stem"] == "a" and first["extension"] == ".csv"
    assert first["size"] == 10 and first["is_folder"] is False
    assert first["path"].endswith("a.csv") and len(first["modified"]) == 19


def test_list_recursive_folders_and_all(inbox):
    assert names(run("file.list", inbox, path="./inbox", pattern="*.csv", recursive=True)) == ["a.csv", "archive/c.csv", "b.csv"]
    assert names(run("file.list", inbox, path="./inbox", type="folders")) == ["archive"]
    assert len(run("file.list", inbox, path="./inbox", type="all")) == 4


def test_list_newest_first_with_limit(inbox):
    newest = run("file.list", inbox, path="./inbox", sort_by="modified", descending="true", limit=1)
    assert names(newest) == ["notes.txt"]
    assert names(run("file.list", inbox, path="./inbox", sort_by="size", descending=True)) == ["b.csv", "a.csv", "notes.txt"]


def test_list_empty_and_errors(inbox):
    assert run("file.list", inbox, path="./inbox", pattern="*.xlsx") == []
    with pytest.raises(FileNotFoundError, match="Folder not found"):
        run("file.list", inbox, path="./missing")
    with pytest.raises(ValueError, match="sort_by"):
        run("file.list", inbox, path="./inbox", sort_by="colour")
    with pytest.raises(ValueError, match="type"):
        run("file.list", inbox, path="./inbox", type="links")


def test_write_then_read_text_lines_and_json(tmp_path):
    run("file.write_text", tmp_path, path="./out/report.txt", content="สรุปรอบนี้\n")
    run("file.write_text", tmp_path, path="./out/report.txt", content="แถวที่ 1", append=True)
    run("file.write_text", tmp_path, path="./out/report.txt", content="แถวที่ 2", append="true")
    assert run("file.read_text", tmp_path, path="./out/report.txt") == "สรุปรอบนี้\nแถวที่ 1\nแถวที่ 2\n"
    assert run("file.read_text", tmp_path, path="./out/report.txt", format="lines") == ["สรุปรอบนี้", "แถวที่ 1", "แถวที่ 2"]

    run("file.write_text", tmp_path, path="data.json", content={"plan": "ชั้น 1", "price": 15900})
    assert run("file.read_text", tmp_path, path="data.json", format="json") == {"plan": "ชั้น 1", "price": 15900}
    assert json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))["plan"] == "ชั้น 1"


def test_write_replaces_unless_append(tmp_path):
    run("file.write_text", tmp_path, path="a.txt", content="first")
    result = run("file.write_text", tmp_path, path="a.txt", content="second")
    assert (tmp_path / "a.txt").read_text(encoding="utf-8") == "second"
    assert result["mode"] == "write" and result["characters_written"] == 6


def test_read_text_with_bom_and_thai_legacy_encoding(tmp_path):
    (tmp_path / "excel.csv").write_bytes("﻿ชื่อ,ราคา\n".encode("utf-8"))
    assert run("file.read_text", tmp_path, path="excel.csv") == "ชื่อ,ราคา\n"

    (tmp_path / "legacy.txt").write_bytes("ประกันภัย".encode("cp874"))
    with pytest.raises(ValueError, match="cp874"):
        run("file.read_text", tmp_path, path="legacy.txt")
    assert run("file.read_text", tmp_path, path="legacy.txt", encoding="cp874") == "ประกันภัย"
    run("file.write_text", tmp_path, path="legacy_out.txt", content="ประกันภัย", encoding="cp874")
    assert (tmp_path / "legacy_out.txt").read_bytes() == "ประกันภัย".encode("cp874")


def test_text_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        run("file.read_text", tmp_path, path="missing.txt")
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        run("file.read_text", tmp_path, path="bad.json", format="json")
    with pytest.raises(ValueError, match="content"):
        run("file.write_text", tmp_path, path="x.txt")
    with pytest.raises(ValueError, match="Unknown encoding"):
        run("file.write_text", tmp_path, path="x.txt", content="a", encoding="klingon")


def test_create_folder(tmp_path):
    assert run("file.create_folder", tmp_path, path="./output/run_1/screens")["created"] is True
    assert run("file.create_folder", tmp_path, path="./output/run_1/screens")["status"] == "exists"
    (tmp_path / "taken").write_text("", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run("file.create_folder", tmp_path, path="taken")


def test_overwrite_false_from_config_text_is_respected(tmp_path):
    (tmp_path / "a.txt").write_text("new", encoding="utf-8")
    (tmp_path / "b.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run("file.copy", tmp_path, source="a.txt", destination="b.txt", overwrite="false")
    with pytest.raises(FileExistsError):
        run("file.move", tmp_path, source="a.txt", destination="b.txt", overwrite="false")
    with pytest.raises(FileNotFoundError):
        run("file.delete", tmp_path, path="missing.txt", missing_ok="false")
    assert (tmp_path / "b.txt").read_text(encoding="utf-8") == "keep"


def test_flow_processes_every_csv_in_an_inbox(inbox):
    flow = markdown_to_flow("""# Process Inbox

## Variables
- `done`: []

## Steps

### 1. Find Order Files (`file.list`)
- **path:** ./inbox
- **pattern:** *.csv
- **output_var:** `files`

### 2. Handle Each File (`logic.loop`)
- **items:** `${files}`
- **item_var:** `f`
- **Sub-steps:**
  - Log File (`file.write_text`):
    - **path:** ./output/processed.txt
    - **content:** ${f.name} (${f.size} bytes)
    - **append:** true
  - Move To Archive (`file.move`):
    - **source:** `${f.path}`
    - **destination:** ./inbox/archive/${f.name}
""")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(inbox)})
    assert not ctx.has_error
    assert (inbox / "output" / "processed.txt").read_text(encoding="utf-8") == "a.csv (10 bytes)\nb.csv (50 bytes)\n"
    assert sorted(p.name for p in (inbox / "inbox" / "archive").iterdir()) == ["a.csv", "b.csv", "c.csv"]

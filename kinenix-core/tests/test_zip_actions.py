"""file.zip and file.unzip: pack a run's files for an email attachment, and unpack received archives."""
import zipfile

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
def output(tmp_path):
    """A flow folder with output/report.csv, output/screenshots/page.png, and a Thai file name."""
    out = tmp_path / "output"
    (out / "screenshots").mkdir(parents=True)
    (out / "report.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (out / "screenshots" / "page.png").write_bytes(b"\x89PNG fake")
    (out / "สรุป.txt").write_text("ประกันภัยชั้น 1", encoding="utf-8")
    return tmp_path


def names(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        return sorted(archive.namelist())


def test_zip_a_folder_keeps_its_structure(output):
    result = run("file.zip", output, source="./output", destination="./mail/run.zip")
    assert result["files_added"] == 3 and result["size_bytes"] > 0
    assert names(output / "mail" / "run.zip") == ["output/report.csv", "output/screenshots/page.png", "output/สรุป.txt"]


def test_zip_inside_the_folder_it_packs_skips_itself(output):
    run("file.zip", output, source="./output", destination="./output/run.zip")
    again = run("file.zip", output, source="./output", destination="./output/run.zip")
    assert again["files_added"] == 3
    assert "output/run.zip" not in names(output / "output" / "run.zip")
    assert not (output / "output" / "run.zip.partial").exists()


def test_zip_a_list_of_files_and_folders(output):
    run("file.zip", output, source=["./output/report.csv", "./output/screenshots"], destination="pack.zip")
    assert names(output / "pack.zip") == ["report.csv", "screenshots/page.png"]


def test_zip_refuses_two_files_with_the_same_name(output):
    (output / "other").mkdir()
    (output / "other" / "report.csv").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="report.csv"):
        run("file.zip", output, source=["./output/report.csv", "./other/report.csv"], destination="pack.zip")


def test_zip_overwrite_false_and_missing_source(output):
    run("file.zip", output, source="./output", destination="run.zip")
    with pytest.raises(FileExistsError):
        run("file.zip", output, source="./output", destination="run.zip", overwrite="false")
    with pytest.raises(FileNotFoundError, match="missing"):
        run("file.zip", output, source="./missing", destination="x.zip")
    with pytest.raises(ValueError, match="required"):
        run("file.zip", output, source="./output")


def test_unzip_round_trip_and_default_destination(output):
    run("file.zip", output, source="./output", destination="run.zip")
    result = run("file.unzip", output, source="run.zip")
    assert result["files_extracted"] == 3
    assert (output / "run" / "output" / "สรุป.txt").read_text(encoding="utf-8") == "ประกันภัยชั้น 1"

    run("file.unzip", output, source="run.zip", destination="./inbox/extracted")
    assert (output / "inbox" / "extracted" / "output" / "screenshots" / "page.png").is_file()


def test_unzip_overwrite_false_stops_before_writing(output):
    run("file.zip", output, source="./output", destination="run.zip")
    run("file.unzip", output, source="run.zip", destination="x")
    with pytest.raises(FileExistsError):
        run("file.unzip", output, source="run.zip", destination="x", overwrite=False)


def test_unzip_rejects_entries_outside_the_destination(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as archive:
        archive.writestr("../escaped.txt", "nope")
    with pytest.raises(ValueError, match="outside the destination"):
        run("file.unzip", tmp_path, source="bad.zip", destination="safe")
    assert not (tmp_path / "escaped.txt").exists()


def test_unzip_errors(tmp_path):
    (tmp_path / "not_a_zip.zip").write_text("plain text", encoding="utf-8")
    with pytest.raises(ValueError, match="Not a zip file"):
        run("file.unzip", tmp_path, source="not_a_zip.zip")
    with pytest.raises(FileNotFoundError):
        run("file.unzip", tmp_path, source="missing.zip")


def test_flow_zips_output_for_an_email(output):
    flow = markdown_to_flow("""# Pack Results

## Steps

### 1. Zip Run Output (`file.zip`)
- **source:** ./output
- **destination:** ./outbox/run.zip
- **output_var:** `packed`

### 2. Attachment Path (`logic.set_variable`)
- **name:** attachment
- **value:** `${packed.zip_path}`
""")
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(output)})
    assert not ctx.has_error
    assert ctx.get_variable("attachment").endswith("run.zip")
    assert (output / "outbox" / "run.zip").is_file()

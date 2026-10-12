"""Issues #49 and #60: subflows share the bundle's config and folder, run from .md, and are validated."""
import json

from kinenix.engine.interpreter import FlowInterpreter
from kinenix.engine.markdown import markdown_to_flow
from kinenix.engine.validation import validate_subflows


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run(bundle, markdown):
    return FlowInterpreter().run_flow(markdown_to_flow(markdown), initial_vars={"__flow_dir__": str(bundle)})


def make_bundle(root, config):
    bundle = root / "bundle"
    write(bundle / "config" / "config.json", json.dumps(config))
    return bundle


WRITER = """# Writer

## Variables
- `label`: unset

## Steps

### 1. Write (`file.write_text`)
- **path:** ./output/from_subflow.txt
- **content:** ${label}|${config.greeting}|${config.extra}
"""


def call(target, extra=""):
    return f"""# Parent

## Steps

### 1. Call (`flow.call`)
- **flow:** {target}
{extra}"""


def test_bundle_subflow_uses_bundle_config_and_folder(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello", "extra": "x"})
    write(bundle / "subflows" / "writer.md", WRITER)
    ctx = run(bundle, call("./subflows/writer.md", '- **inputs:** {"label": "A"}\n'))
    assert not ctx.has_error, ctx.failure_details
    assert (bundle / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "A|Hello|x"
    assert not (bundle / "subflows" / "output").exists()


def test_inputs_config_is_merged_over_the_bundle_config(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello", "extra": "x"})
    write(bundle / "subflows" / "writer.md", WRITER)
    run(bundle, call("./subflows/writer.md", '- **inputs:** {"label": "B", "config": {"extra": "override"}}\n'))
    assert (bundle / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "B|Hello|override"


def test_shared_subflow_keeps_its_own_folder_and_config(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello", "extra": "x"})
    shared = tmp_path / "@shared"
    write(shared / "writer.md", WRITER)
    write(shared / "config" / "config.json", json.dumps({"greeting": "Shared", "extra": "own"}))

    run(bundle, call("@shared/writer.md"))
    assert (shared / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "unset|Shared|own"
    assert not (bundle / "output").exists()


def test_inherit_config_gives_a_shared_subflow_the_callers_config(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello"})
    shared = tmp_path / "@shared"
    write(shared / "writer.md", WRITER)
    write(shared / "config" / "config.json", json.dumps({"greeting": "Shared", "extra": "own default"}))

    run(bundle, call("@shared/writer.md", "- **inherit_config:** true\n"))
    # The caller's keys win; keys only the shared subflow defines stay as its defaults
    assert (shared / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "unset|Hello|own default"


def test_md_source_wins_over_a_stale_json_and_extensionless_targets_work(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello", "extra": "x"})
    write(bundle / "subflows" / "writer.md", WRITER)
    stale = markdown_to_flow(WRITER.replace("${label}|", "STALE|"))
    write(bundle / "subflows" / "writer.json", stale.model_dump_json())
    run(bundle, call("./subflows/writer", '- **inputs:** {"label": "C"}\n'))
    assert (bundle / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "C|Hello|x"


def test_a_subflow_can_call_a_sibling_by_a_path_relative_to_itself(tmp_path):
    bundle = make_bundle(tmp_path, {"greeting": "Hello", "extra": "x"})
    write(bundle / "subflows" / "writer.md", WRITER)
    write(bundle / "subflows" / "outer.md", call("./writer.md", '- **inputs:** {"label": "D"}\n'))
    ctx = run(bundle, call("./subflows/outer.md"))
    assert not ctx.has_error, ctx.failure_details
    assert (bundle / "output" / "from_subflow.txt").read_text(encoding="utf-8") == "D|Hello|x"


def test_validate_follows_subflows(tmp_path):
    bundle = make_bundle(tmp_path, {})
    write(bundle / "subflows" / "writer.md", WRITER + "this line is not a parameter\n")
    write(bundle / "subflows" / "loop_a.md", call("./subflows/loop_b.md"))
    write(bundle / "subflows" / "loop_b.md", call("./subflows/loop_a.md"))
    flow = markdown_to_flow("""# Parent

## Steps

### 1. Wrong Input Name (`flow.call`)
- **flow:** ./subflows/writer.md
- **inputs:** {"lable": "A", "config": {}}

### 2. Missing (`flow.call`)
- **flow:** ./subflows/nope.md

### 3. Dynamic Target Is Skipped (`flow.call`)
- **flow:** ./subflows/${which}.md

### 4. Calls That Loop (`flow.call`)
- **flow:** ./subflows/loop_a.md
""")
    issues = validate_subflows(flow, bundle)
    text = "\n".join(issues)
    assert "input 'lable' is not declared" in text and "Did you mean 'label'?" in text
    assert "'./subflows/nope.md' was not found" in text
    assert "Subflow './subflows/writer.md': Line" in text and "not a parameter" in text
    assert "${which}" not in text
    assert len(issues) == 3


def test_hello_example_calls_its_subflow(tmp_path):
    from kinenix import scaffold

    project = scaffold.create_project(tmp_path / "hello")
    assert (project / "subflows" / "make_greeting.md").is_file()
    flow = markdown_to_flow((project / "flow.md").read_text(encoding="utf-8"))
    assert validate_subflows(flow, project) == []
    ctx = FlowInterpreter().run_flow(flow, initial_vars={"__flow_dir__": str(project)})
    assert not ctx.has_error, ctx.failure_details
    assert "Hello, Malee!" in (project / "output" / "greetings.csv").read_text(encoding="utf-8-sig")

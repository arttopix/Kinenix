import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..models.flow import FlowDefinition, Step, ErrorHandlerConfig


_ACTION_REGEX = re.compile(r"\(\s*`?([a-zA-Z0-9_\.]+)`?\s*\)")
_STEP_HEADING_REGEX = re.compile(
    r"^###\s+(?:(?P<idx>[\w\.\-]+)\.\s+)?(?P<name>.+?)\s*\(\s*`?(?P<action>[a-zA-Z0-9_\.]+)`?\s*\)\s*$"
)
_CHILD_STEP_REGEX = re.compile(
    r"^-\s+(?:(?P<idx>[\w\.\-]+)\.\s+)?(?P<name>.+?)\s*\(\s*`?(?P<action>[a-zA-Z0-9_\.]+)`?\s*\)\s*:?\s*$"
)
_PARAM_REGEX = re.compile(
    r"^-\s+\*\*(?P<key>[a-zA-Z0-9_]+):?\*\*:?\s*(?P<val>.*)$"
)
_ALT_PARAM_REGEX = re.compile(
    r"^-\s+(?P<key>[a-zA-Z0-9_]+):\s*(?P<val>.*)$"
)
_SUB_STEPS_REGEX = re.compile(
    r"^-\s+\*\*(?:Sub-steps|sub_steps):?\*\*:?\s*$", re.IGNORECASE
)
_ELSE_STEPS_REGEX = re.compile(
    r"^-\s+\*\*(?:Else-steps|else_steps):?\*\*:?\s*$", re.IGNORECASE
)
_ALT_SUB_STEPS_REGEX = re.compile(
    r"^-\s+(?:Sub-steps|sub_steps):\s*$", re.IGNORECASE
)
_ALT_ELSE_STEPS_REGEX = re.compile(
    r"^-\s+(?:Else-steps|else_steps):\s*$", re.IGNORECASE
)

# Step keys that configure retry and failure behavior; they belong to Step.error_handler, not to the
# action parameters, because the interpreter reads them from error_handler only
ERROR_HANDLER_KEYS = ("on_error", "max_retries", "retry_interval", "fallback_step_id")


# A parameter written as `- **body:** |` takes the indented lines below it as its value
BLOCK_MARKER = "|"

Line = Tuple[int, str, int]  # (indent, stripped text, line number)


def _block_value(body_lines: List[Line], start: int, key_indent: int) -> Tuple[Optional[str], int]:
    """
    Reads a multi-line value: the blank or more deeply indented lines from `start` on. Their common
    indentation is removed, relative indentation and blank lines inside are kept, and blank lines at
    the end are dropped. Returns (None, start) when no indented line follows, so a lone `|` stays a value.
    """
    end = start
    while end < len(body_lines) and (not body_lines[end][1] or body_lines[end][0] > key_indent):
        end += 1
    collected = body_lines[start:end]
    while collected and not collected[-1][1]:
        collected.pop()
    if not collected:
        return None, start
    base = min(indent for indent, text, _ in collected if text)
    text = "\n".join(" " * (indent - base) + line if line else "" for indent, line, _ in collected)
    return text, start + len(collected)


def _stray_line_issue(lineno: int, text: str, step_name: str) -> str:
    shown = text if len(text) <= 60 else text[:57] + "..."
    return (f"Line {lineno}: '{shown}' in step '{step_name}' is not a parameter and was ignored. "
            f"For a value with several lines, write the parameter as `- **name:** |` and indent the lines below it.")


def _param_lines(pad: str, key: str, value: Any) -> List[str]:
    """Markdown lines for one parameter; text with line breaks is written as a `|` block."""
    if isinstance(value, str) and "\n" in value:
        inner = pad + "    "
        return [f"{pad}- **{key}:** {BLOCK_MARKER}"] + [inner + line if line else "" for line in value.split("\n")]
    return [f"{pad}- **{key}:** {format_value(value)}"]


def _error_handler_lines(step: Step, pad: str) -> List[str]:
    if not step.error_handler:
        return []
    values = step.error_handler.model_dump(exclude_defaults=True)
    return [f"{pad}- **{key}:** {format_value(values[key])}" for key in ERROR_HANDLER_KEYS if key in values]


def parse_value(val_str: str) -> Any:
    """Parse a string into a typed Python value (bool, int, float, json, or str)."""
    val_str = val_str.strip()
    if not val_str:
        return ""

    # Strip enclosing inline backticks, e.g. `challenge_data` -> challenge_data
    if val_str.startswith("`") and val_str.endswith("`") and len(val_str) >= 2:
        val_str = val_str[1:-1].strip()

    # Booleans and Null
    low = val_str.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "none"):
        return None

    # Integers
    if re.match(r"^-?\d+$", val_str):
        try:
            return int(val_str)
        except ValueError:
            pass

    # Floats
    if re.match(r"^-?\d+\.\d+$", val_str):
        try:
            return float(val_str)
        except ValueError:
            pass

    # JSON Objects / Arrays
    if (val_str.startswith("{") and val_str.endswith("}")) or (val_str.startswith("[") and val_str.endswith("]")):
        try:
            return json.loads(val_str)
        except Exception:
            pass

    # Quoted strings: "string" or 'string'
    if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
        if len(val_str) >= 2:
            return val_str[1:-1]

    return val_str


def format_value(val: Any) -> str:
    """Format a Python value into markdown representation."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if val is None:
        return "null"
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    if isinstance(val, (int, float)):
        return str(val)
    # If variable expression like ${foo}, keep as is
    return str(val)


def _parse_sub_steps_block(lines: List[Line], parent_id: str, issues: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Recursively parse indented sub-steps from lines formatted as: (indent, raw_stripped_text, line_number).
    Blank lines are kept, because they belong to multi-line values.
    """
    if not lines:
        return []

    # Filter out blank lines
    non_blank = [item for item in lines if item[1]]
    if not non_blank:
        return []

    min_indent = min(item[0] for item in non_blank)
    
    # Group steps at min_indent
    steps: List[Dict[str, Any]] = []
    current_step_lines: List[Tuple[int, str, int]] = []
    current_match = None

    def finalize_step(match, body_lines, step_idx):
        idx_val = match.group("idx")
        name = match.group("name").strip()
        action = match.group("action").strip()

        step_id = idx_val if idx_val else f"{parent_id}_{step_idx}"
        if not step_id.startswith("step_") and not step_id.startswith("sub_"):
            step_id = f"sub_{step_id}"

        step_dict: Dict[str, Any] = {
            "id": step_id,
            "name": name,
            "action": action,
            "parameters": {},
        }

        # Parse body_lines
        i = 0
        while i < len(body_lines):
            indent, text, lineno = body_lines[i]
            
            # Check for Sub-steps:
            sub_match = _SUB_STEPS_REGEX.match(text) or _ALT_SUB_STEPS_REGEX.match(text)
            else_match = _ELSE_STEPS_REGEX.match(text) or _ALT_ELSE_STEPS_REGEX.match(text)

            if not text:
                i += 1
                continue

            if sub_match:
                # Collect all subsequent lines that have higher indentation
                sub_lines = []
                i += 1
                while i < len(body_lines) and (body_lines[i][0] > indent or not body_lines[i][1]):
                    sub_lines.append(body_lines[i])
                    i += 1
                sub_parsed = _parse_sub_steps_block(sub_lines, parent_id=step_id, issues=issues)
                if sub_parsed:
                    step_dict["sub_steps"] = sub_parsed
                continue

            elif else_match:
                else_lines = []
                i += 1
                while i < len(body_lines) and (body_lines[i][0] > indent or not body_lines[i][1]):
                    else_lines.append(body_lines[i])
                    i += 1
                else_parsed = _parse_sub_steps_block(else_lines, parent_id=f"{step_id}_else", issues=issues)
                if else_parsed:
                    step_dict["else_steps"] = else_parsed
                continue

            # Check for parameters
            param_match = _PARAM_REGEX.match(text) or _ALT_PARAM_REGEX.match(text)
            if param_match:
                key = param_match.group("key")
                val_raw = param_match.group("val")
                val = parse_value(val_raw)
                if val_raw.strip() == BLOCK_MARKER:
                    block, next_i = _block_value(body_lines, i + 1, indent)
                    if block is not None:
                        val_raw, val = block, block
                        i = next_i - 1

                if key == "output_var":
                    step_dict["output_var"] = str(val) if val is not None else None
                elif key == "condition":
                    cond_val = str(val_raw).strip()
                    if cond_val.startswith("`") and cond_val.endswith("`") and len(cond_val) >= 2:
                        cond_val = cond_val[1:-1].strip()
                    step_dict["condition"] = cond_val
                elif key == "description":
                    step_dict["description"] = str(val)
                elif key == "id":
                    step_dict["id"] = str(val)
                elif key in ERROR_HANDLER_KEYS:
                    step_dict.setdefault("error_handler", {})[key] = val
                elif key == "error_handler" and isinstance(val, dict):
                    step_dict.setdefault("error_handler", {}).update(val)
                else:
                    step_dict["parameters"][key] = val
            elif issues is not None:
                issues.append(_stray_line_issue(lineno, text, name))
            i += 1

        return step_dict

    child_counter = 1
    for indent, text, lineno in lines:
        if text and indent == min_indent:
            match = _CHILD_STEP_REGEX.match(text)
            if match:
                if current_match:
                    steps.append(finalize_step(current_match, current_step_lines, child_counter))
                    child_counter += 1
                current_match = match
                current_step_lines = []
                continue
        if current_match:
            current_step_lines.append((indent, text, lineno))
        elif text and issues is not None:
            issues.append(f"Line {lineno}: '{text[:60]}' is not a sub-step; a sub-step looks like `- Name (`action.name`):`.")

    if current_match:
        steps.append(finalize_step(current_match, current_step_lines, child_counter))

    return steps


def markdown_to_flow(md_content: str, issues: Optional[List[str]] = None) -> FlowDefinition:
    """
    Parses a Flow Markdown specification string into a validated FlowDefinition.
    Adheres strictly to docs/flow_markdown_spec.md. When `issues` is a list, lines that were ignored
    (text under a step that is not a parameter) are reported in it.
    """
    # Tabs count as four spaces, so indentation typed with Tab works like spaces
    lines = [line.expandtabs(4) for line in md_content.splitlines()]
    
    flow_name = "Untitled Flow"
    description: Optional[str] = None
    version = "1.0.0"
    variables: Dict[str, Any] = {}

    in_variables_section = False
    in_steps_section = False

    raw_steps: List[Tuple[Optional[re.Match], List[Tuple[int, str, int]]]] = []
    current_step_match: Optional[re.Match] = None
    current_step_lines: List[Tuple[int, str, int]] = []

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        # 1. Level 1 Heading: Flow Title
        if stripped.startswith("# ") and not in_steps_section:
            flow_name = stripped[2:].strip()
            continue

        # 2. Blockquotes: Description and Version
        if stripped.startswith(">") and not in_steps_section:
            quote_text = stripped[1:].strip()
            if quote_text.lower().startswith("description:"):
                description = quote_text[len("description:"):].strip()
            elif quote_text.lower().startswith("version:"):
                version = quote_text[len("version:"):].strip()
            continue

        # 3. Section headers
        if stripped.startswith("## "):
            sec_title = stripped[3:].strip().lower()
            if "variable" in sec_title:
                in_variables_section = True
                in_steps_section = False
                continue
            elif "step" in sec_title:
                in_steps_section = True
                in_variables_section = False
                continue

        # 4. Variables section
        if in_variables_section and not in_steps_section:
            if stripped.startswith("-"):
                # Format: - `var_name`: value or - var_name: value
                v_match = re.match(r"^-\s+(?:`(?P<key>[^`]+)`|(?P<key2>[a-zA-Z0-9_]+)):\s*(?P<val>.*)$", stripped)
                if v_match:
                    k = v_match.group("key") or v_match.group("key2")
                    v_raw = v_match.group("val")
                    variables[k] = parse_value(v_raw)
                continue

        # 5. Steps section: Level 3 Headings
        step_match = _STEP_HEADING_REGEX.match(stripped)
        if step_match:
            in_steps_section = True
            in_variables_section = False
            if current_step_match:
                raw_steps.append((current_step_match, current_step_lines))
            current_step_match = step_match
            current_step_lines = []
            continue

        if in_steps_section and current_step_match:
            current_step_lines.append((indent, stripped, lineno))

    if current_step_match:
        raw_steps.append((current_step_match, current_step_lines))

    # Process all steps
    compiled_steps: List[Dict[str, Any]] = []
    step_counter = 1

    for match, body_lines in raw_steps:
        idx_val = match.group("idx")
        name = match.group("name").strip()
        action = match.group("action").strip()

        if idx_val:
            if idx_val.isdigit():
                step_id = f"step_{idx_val}"
            else:
                step_id = idx_val
        else:
            step_id = f"step_{step_counter}"

        step_counter += 1

        step_dict: Dict[str, Any] = {
            "id": step_id,
            "name": name,
            "action": action,
            "parameters": {},
        }

        i = 0
        while i < len(body_lines):
            indent, text, lineno = body_lines[i]
            if not text:
                i += 1
                continue

            sub_match = _SUB_STEPS_REGEX.match(text) or _ALT_SUB_STEPS_REGEX.match(text)
            else_match = _ELSE_STEPS_REGEX.match(text) or _ALT_ELSE_STEPS_REGEX.match(text)

            if sub_match:
                sub_lines = []
                i += 1
                while i < len(body_lines) and (body_lines[i][0] > indent or not body_lines[i][1]):
                    sub_lines.append(body_lines[i])
                    i += 1
                sub_parsed = _parse_sub_steps_block(sub_lines, parent_id=f"sub_{step_id}", issues=issues)
                if sub_parsed:
                    step_dict["sub_steps"] = sub_parsed
                continue

            elif else_match:
                else_lines = []
                i += 1
                while i < len(body_lines) and (body_lines[i][0] > indent or not body_lines[i][1]):
                    else_lines.append(body_lines[i])
                    i += 1
                else_parsed = _parse_sub_steps_block(else_lines, parent_id=f"sub_{step_id}_else", issues=issues)
                if else_parsed:
                    step_dict["else_steps"] = else_parsed
                continue

            param_match = _PARAM_REGEX.match(text) or _ALT_PARAM_REGEX.match(text)
            if param_match:
                key = param_match.group("key")
                val_raw = param_match.group("val")
                val = parse_value(val_raw)
                if val_raw.strip() == BLOCK_MARKER:
                    block, next_i = _block_value(body_lines, i + 1, indent)
                    if block is not None:
                        val_raw, val = block, block
                        i = next_i - 1

                if key == "output_var":
                    step_dict["output_var"] = str(val) if val is not None else None
                elif key == "condition":
                    cond_val = str(val_raw).strip()
                    if cond_val.startswith("`") and cond_val.endswith("`") and len(cond_val) >= 2:
                        cond_val = cond_val[1:-1].strip()
                    step_dict["condition"] = cond_val
                elif key == "description":
                    step_dict["description"] = str(val)
                elif key == "id":
                    step_dict["id"] = str(val)
                elif key in ERROR_HANDLER_KEYS:
                    step_dict.setdefault("error_handler", {})[key] = val
                elif key == "error_handler" and isinstance(val, dict):
                    step_dict.setdefault("error_handler", {}).update(val)
                else:
                    step_dict["parameters"][key] = val
            elif issues is not None:
                issues.append(_stray_line_issue(lineno, text, name))
            i += 1

        compiled_steps.append(step_dict)

    flow_payload = {
        "name": flow_name,
        "description": description,
        "version": version,
        "variables": variables,
        "steps": compiled_steps,
    }

    return FlowDefinition.model_validate(flow_payload)


def _serialize_sub_steps(steps: List[Step], indent_spaces: int = 2) -> List[str]:
    """Serializes child steps recursively with indentation."""
    lines: List[str] = []
    pad = " " * indent_spaces
    param_pad = " " * (indent_spaces + 2)

    for s in steps:
        lines.append(f"{pad}- {s.name} (`{s.action}`):")
        if s.description:
            lines.append(f"{param_pad}- **description:** {s.description}")
        if s.condition:
            lines.append(f"{param_pad}- **condition:** {s.condition}")
        if s.output_var:
            lines.append(f"{param_pad}- **output_var:** `{s.output_var}`")
        for k, v in s.parameters.items():
            lines.extend(_param_lines(param_pad, k, v))
        lines.extend(_error_handler_lines(s, param_pad))

        if s.sub_steps:
            lines.append(f"{param_pad}- **Sub-steps:**")
            lines.extend(_serialize_sub_steps(s.sub_steps, indent_spaces=indent_spaces + 4))
        if s.else_steps:
            lines.append(f"{param_pad}- **Else-steps:**")
            lines.extend(_serialize_sub_steps(s.else_steps, indent_spaces=indent_spaces + 4))

    return lines


def flow_to_markdown(flow: FlowDefinition) -> str:
    """
    Serializes a FlowDefinition into a formatted flow.md specification string.
    Adheres strictly to docs/flow_markdown_spec.md.
    """
    doc: List[str] = []

    # Title & Metadata
    doc.append(f"# {flow.name}")
    if flow.description:
        doc.append(f"> Description: {flow.description}")
    doc.append(f"> Version: {flow.version}")
    doc.append("")

    # Variables
    if flow.variables:
        doc.append("## Variables")
        for k, v in flow.variables.items():
            doc.append(f"- `{k}`: {format_value(v)}")
        doc.append("")

    # Steps
    doc.append("## Steps")
    doc.append("")

    for idx, step in enumerate(flow.steps, start=1):
        step_idx_str = str(idx)
        if step.id and step.id.startswith("step_") and step.id[5:].isdigit():
            step_idx_str = step.id[5:]
        elif step.id:
            step_idx_str = step.id

        doc.append(f"### {step_idx_str}. {step.name} (`{step.action}`)")
        
        if step.description:
            doc.append(f"- **description:** {step.description}")
        if step.condition:
            doc.append(f"- **condition:** {step.condition}")
        if step.output_var:
            doc.append(f"- **output_var:** `{step.output_var}`")
        for k, v in step.parameters.items():
            doc.extend(_param_lines("", k, v))
        doc.extend(_error_handler_lines(step, ""))

        if step.sub_steps:
            doc.append("- **Sub-steps:**")
            doc.extend(_serialize_sub_steps(step.sub_steps, indent_spaces=2))
        if step.else_steps:
            doc.append("- **Else-steps:**")
            doc.extend(_serialize_sub_steps(step.else_steps, indent_spaces=2))

        doc.append("")

    return "\n".join(doc).rstrip() + "\n"


def markdown_issues(md_content: str) -> List[str]:
    """Lines of a flow.md that the compiler ignores, as human-readable problems."""
    issues: List[str] = []
    markdown_to_flow(md_content, issues=issues)
    return issues


def load_flow(path_or_content: Union[str, Path]) -> FlowDefinition:
    """
    Smart flow loader that accepts:
    - Path to a flow.md or flow.json file
    - Path to a bundle directory containing flow.md or flow.json
    - Raw string content (Markdown or JSON)
    """
    if isinstance(path_or_content, Path) or (isinstance(path_or_content, str) and "\n" not in path_or_content and Path(path_or_content).exists()):
        p = Path(path_or_content).resolve()
        if p.is_dir():
            if (p / "flow.md").is_file():
                return markdown_to_flow((p / "flow.md").read_text(encoding="utf-8-sig"))
            elif (p / "flow.json").is_file():
                raw = json.loads((p / "flow.json").read_text(encoding="utf-8-sig"))
                return FlowDefinition.model_validate(raw)
            else:
                raise FileNotFoundError(f"Neither flow.md nor flow.json found in bundle directory: {p}")
        
        if p.suffix.lower() == ".md":
            return markdown_to_flow(p.read_text(encoding="utf-8-sig"))
        elif p.suffix.lower() == ".json":
            raw = json.loads(p.read_text(encoding="utf-8-sig"))
            return FlowDefinition.model_validate(raw)
        else:
            raise ValueError(f"Unsupported flow file extension: {p.suffix} (expected .md or .json)")

    # Raw string content
    content = str(path_or_content).strip()
    if content.startswith("{"):
        raw = json.loads(content)
        return FlowDefinition.model_validate(raw)
    else:
        return markdown_to_flow(content)


def compile_markdown_to_json(md_path: Path, output_json_path: Optional[Path] = None) -> Path:
    """
    Compiles a flow.md file into a validated flow.json.
    """
    md_path = md_path.resolve()
    if not md_path.is_file():
        raise FileNotFoundError(f"Markdown flow file not found: {md_path}")

    flow = markdown_to_flow(md_path.read_text(encoding="utf-8-sig"))
    
    if output_json_path is None:
        output_json_path = md_path.parent / "flow.json"
    else:
        output_json_path = output_json_path.resolve()

    schema_ref = "../../../schemas/flow.schema.json"
    data = flow.model_dump(exclude_none=True)
    
    # Prepend $schema for IDE autocomplete if not present
    ordered_data = {"$schema": schema_ref}
    ordered_data.update(data)

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(ordered_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    return output_json_path


class FlowSync:
    """Results of sync_flow_json."""
    NO_MARKDOWN = "no_markdown"    # flow.json has no flow.md next to it; nothing to do
    UP_TO_DATE = "up_to_date"      # flow.json already matches flow.md
    CREATED = "created"            # flow.json did not exist and was compiled
    COMPILED = "compiled"          # flow.md changed after flow.json; flow.json was recompiled
    JSON_NEWER = "json_newer"      # flow.json was edited after flow.md (e.g. in Studio); left untouched


def _same_flow(a: FlowDefinition, b: FlowDefinition) -> bool:
    return a.model_dump(exclude_none=True) == b.model_dump(exclude_none=True)


def sync_flow_json(md_path: Path) -> str:
    """Keep the build artifact flow.json in line with its source flow.md before a run.

    flow.md is the source of truth. The files are compared by content, not timestamps, because
    git checkouts reset modification times. When they differ, timestamps only decide the direction:
    a newer flow.md is recompiled; a newer flow.json was edited directly and is left untouched so
    the edit is not lost (the caller should warn). Returns a FlowSync value.
    """
    md_path = Path(md_path).resolve()
    json_path = md_path.parent / "flow.json"
    if not md_path.is_file():
        return FlowSync.NO_MARKDOWN

    if not json_path.is_file():
        compile_markdown_to_json(md_path, json_path)
        return FlowSync.CREATED

    md_flow = markdown_to_flow(md_path.read_text(encoding="utf-8-sig"))
    try:
        json_flow = FlowDefinition.model_validate(json.loads(json_path.read_text(encoding="utf-8-sig")))
    except (ValueError, OSError):
        json_flow = None  # unreadable or invalid flow.json is rebuilt from the source
    if json_flow is not None and _same_flow(md_flow, json_flow):
        return FlowSync.UP_TO_DATE

    if json_flow is not None and json_path.stat().st_mtime > md_path.stat().st_mtime:
        return FlowSync.JSON_NEWER

    compile_markdown_to_json(md_path, json_path)
    return FlowSync.COMPILED


def export_json_to_markdown(json_path: Path, output_md_path: Optional[Path] = None) -> Path:
    """
    Exports a flow.json file into a human-readable flow.md.
    """
    json_path = json_path.resolve()
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON flow file not found: {json_path}")

    raw = json.loads(json_path.read_text(encoding="utf-8-sig"))
    flow = FlowDefinition.model_validate(raw)
    md_text = flow_to_markdown(flow)

    if output_md_path is None:
        output_md_path = json_path.parent / "flow.md"
    else:
        output_md_path = output_md_path.resolve()

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.write_text(md_text, encoding="utf-8")
    return output_md_path

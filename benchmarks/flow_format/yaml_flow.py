"""Prototype used only by this benchmark: read a flow.yaml into the FlowDefinition Kinenix runs.

Kinenix itself does not read YAML; see docs/benchmarks/flow_format.md for why.
"""
from typing import Any, Dict, List

import yaml

from kinenix.models.flow import FlowDefinition

STEP_KEYS = {"id", "name", "action", "with", "output_var", "condition", "description",
             "on_error", "max_retries", "retry_interval", "fallback_step_id", "steps", "else"}
ERROR_KEYS = ("on_error", "max_retries", "retry_interval", "fallback_step_id")


def _step(raw: Dict[str, Any], step_id: str, problems: List[str]) -> Dict[str, Any]:
    unknown = set(raw) - STEP_KEYS
    if unknown:
        problems.append(f"{step_id} ({raw.get('name')}): unknown keys {sorted(unknown)} (parameters go under 'with:')")
    step = {"id": raw.get("id") or step_id, "name": raw.get("name", ""), "action": raw.get("action", ""),
            "parameters": dict(raw.get("with") or {})}
    for key in ("output_var", "condition", "description"):
        if key in raw:
            step[key] = raw[key]
    handler = {k: raw[k] for k in ERROR_KEYS if k in raw}
    if handler:
        step["error_handler"] = handler
    parent = step["id"]
    if raw.get("steps"):
        step["sub_steps"] = [_step(s, f"sub_{parent}_{i}", problems) for i, s in enumerate(raw["steps"], 1)]
    if raw.get("else"):
        step["else_steps"] = [_step(s, f"sub_{parent}_else_{i}", problems) for i, s in enumerate(raw["else"], 1)]
    return step


def yaml_to_flow(text: str, problems: List[str] = None) -> FlowDefinition:
    problems = problems if problems is not None else []
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("flow.yaml must be a mapping with name and steps")
    steps = [_step(s, f"step_{i}", problems) for i, s in enumerate(data.get("steps") or [], 1)]
    return FlowDefinition.model_validate({
        "name": data.get("name", "Untitled Flow"), "description": data.get("description"),
        "version": str(data.get("version", "1.0.0")), "variables": data.get("variables") or {}, "steps": steps})

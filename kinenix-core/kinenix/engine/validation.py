"""Static checks on a flow before it runs: unknown actions and parameters that no action reads.

A misspelled parameter (for example `timout`) is otherwise ignored silently and the action falls back to
its default, which is hard to notice. These checks only report; callers decide whether to warn or stop.
"""
import difflib
from pathlib import Path
from typing import Iterable, List, Optional, Set

from .. import actions  # noqa: F401  (imports every action module so the registry is complete)
from ..actions.registry import ActionRegistry
from ..models.flow import FlowDefinition, Step

# Keys that belong to the step itself; seeing them in parameters means the flow.json was written by hand
STEP_LEVEL_KEYS = {
    "on_error": "error_handler",
    "max_retries": "error_handler",
    "retry_interval": "error_handler",
    "fallback_step_id": "error_handler",
    "output_var": "the step's output_var",
    "condition": "the step's condition",
}


def _walk(steps: Iterable[Step]) -> Iterable[Step]:
    for step in steps or []:
        yield step
        yield from _walk(step.sub_steps)
        yield from _walk(step.else_steps)


def validate_flow(flow: FlowDefinition) -> List[str]:
    """Return human-readable problems found in the flow; an empty list means none."""
    issues: List[str] = []
    known_actions = ActionRegistry.list_actions()

    for step in _walk(flow.steps):
        where = f"Step '{step.id}' ({step.name})"
        action_cls = known_actions.get(step.action)
        if action_cls is None:
            close = difflib.get_close_matches(step.action, known_actions, n=1)
            hint = f" Did you mean '{close[0]}'?" if close else ""
            issues.append(f"{where}: unknown action '{step.action}'.{hint}")
            continue

        accepted = action_cls.accepted_parameters
        if accepted is None:
            continue
        # logic.if reads 'condition' as a parameter, so step-level hints apply only to keys it does not accept
        for key in step.parameters:
            if key in accepted:
                continue
            if key in STEP_LEVEL_KEYS:
                issues.append(
                    f"{where}: '{key}' is in parameters, where {step.action} ignores it; "
                    f"it belongs in {STEP_LEVEL_KEYS[key]}. Write it in flow.md and recompile."
                )
                continue
            close = difflib.get_close_matches(key, accepted, n=1)
            hint = f" Did you mean '{close[0]}'?" if close else f" Accepted: {', '.join(accepted) or 'none'}."
            issues.append(f"{where}: {step.action} does not use parameter '{key}'; it would be ignored.{hint}")
    return issues


class _BundleVariables:
    """Just enough of an ExecutionContext for resolving flow.call targets without running anything."""

    def __init__(self, flow_dir: Path, flow_file_dir: Path):
        self._values = {"__flow_dir__": str(flow_dir), "__flow_file_dir__": str(flow_file_dir)}

    def get_variable(self, name: str):
        return self._values.get(name)


def validate_subflows(flow: FlowDefinition, flow_dir: Path, flow_file_dir: Optional[Path] = None,
                      _seen: Optional[Set[Path]] = None) -> List[str]:
    """
    Follows every flow.call whose target is a fixed path, and reports problems in the subflows:
    files that cannot be found, the subflow's own problems (including lines a .md subflow ignores),
    and `inputs` the subflow does not declare in its ## Variables. Targets built from ${...} are skipped.
    """
    from .interpreter import is_shared_subflow, load_subflow, resolve_subflow_path
    from .markdown import markdown_issues

    issues: List[str] = []
    seen = _seen if _seen is not None else set()
    flow_file_dir = flow_file_dir or flow_dir
    for step in _walk(flow.steps):
        if step.action != "flow.call":
            continue
        target = step.parameters.get("flow")
        where = f"Step '{step.id}' ({step.name})"
        if not isinstance(target, str) or "${" in target:
            continue
        try:
            path = resolve_subflow_path(target, _BundleVariables(flow_dir, flow_file_dir))
        except FileNotFoundError:
            issues.append(f"{where}: subflow '{target}' was not found.")
            continue
        try:
            child = load_subflow(path)
        except Exception as exc:
            issues.append(f"{where}: subflow '{target}' could not be read: {exc}")
            continue

        inputs = step.parameters.get("inputs")
        if isinstance(inputs, dict):
            declared = set(child.variables)
            for key in inputs:
                if key == "config" or key in declared:
                    continue
                close = difflib.get_close_matches(key, declared, n=1)
                hint = (f" Did you mean '{close[0]}'?" if close
                        else f" It declares: {', '.join(sorted(declared)) or 'nothing'}.")
                issues.append(f"{where}: input '{key}' is not declared in the ## Variables of subflow '{target}'.{hint}")

        if path in seen:
            continue  # each subflow is checked once, also when flows call each other in a loop
        seen.add(path)
        prefix = f"Subflow '{target}': "
        if path.suffix.lower() == ".md":
            issues.extend(prefix + issue for issue in markdown_issues(path.read_text(encoding="utf-8-sig")))
        issues.extend(prefix + issue for issue in validate_flow(child))
        shared = is_shared_subflow(target, path, _BundleVariables(flow_dir, flow_file_dir))
        child_dir = path.parent if shared else flow_dir
        issues.extend(validate_subflows(child, child_dir, path.parent, seen))
    return issues

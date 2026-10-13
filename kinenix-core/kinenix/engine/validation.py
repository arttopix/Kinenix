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
from .requires import requirement_problem

# Keys that belong to the step itself; seeing them in parameters means a converted flow or a typo put them there
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


def _all_steps(flow: FlowDefinition) -> List[Step]:
    """Steps, On Error, and Finally, in that order."""
    return list(flow.steps) + list(flow.on_error_steps or []) + list(flow.finally_steps or [])


ON_ERROR_VALUES = ("fail", "stop", "retry", "continue")
# What the flow uses that Kinenix 0.2.0b3 and older would run wrongly (item_label is only ignored, so it is not listed)
NEEDS_0_2_0B4 = "kinenix>=0.2.0b4"


def _newer_features(flow: FlowDefinition) -> List[str]:
    used = []
    if flow.on_error_steps:
        used.append("## On Error")
    if flow.finally_steps:
        used.append("## Finally")
    steps = list(_walk(_all_steps(flow)))
    if any(s.action == "flow.call" and "inherit_config" in s.parameters for s in steps):
        used.append("inherit_config")
    return used


def validate_flow(flow: FlowDefinition) -> List[str]:
    """Return human-readable problems found in the flow; an empty list means none."""
    issues: List[str] = []
    known_actions = ActionRegistry.list_actions()

    problem = requirement_problem(flow.requires)
    if problem:
        issues.append(problem)
    used = _newer_features(flow)
    if used and not flow.requires:
        issues.append(
            f"The flow uses {', '.join(used)}, which Kinenix 0.2.0b3 and older do not understand: they run "
            f"On Error and Finally steps as ordinary steps and ignore inherit_config. Add "
            f"`> Requires: {NEEDS_0_2_0B4}` under the title, so older workers refuse the flow instead.")

    for step in _walk(_all_steps(flow)):
        where = f"Step '{step.id}' ({step.name})"
        on_error = step.error_handler.on_error if step.error_handler else None
        if on_error is not None and str(on_error).strip().lower() not in ON_ERROR_VALUES:
            issues.append(f"{where}: on_error '{on_error}' is not one of {', '.join(ON_ERROR_VALUES)}; "
                          f"it would stop the flow like fail.")
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
    for step in _walk(_all_steps(flow)):
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

"""Static checks on a flow before it runs: unknown actions and parameters that no action reads.

A misspelled parameter (for example `timout`) is otherwise ignored silently and the action falls back to
its default, which is hard to notice. These checks only report; callers decide whether to warn or stop.
"""
import difflib
from pathlib import Path
from typing import Any, Iterable, List, Optional, Set

from .. import actions  # noqa: F401  (imports every action module so the registry is complete)
from ..actions.registry import ActionRegistry
from ..models.flow import FlowDefinition, Step
from . import expressions
from .evaluator import VariableEvaluator
from .requires import requirement_problem, version_key

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

# What older Kinenix versions would run wrongly instead of refusing: feature -> (first version that
# understands it, the last version that does not, what the older version does). item_label is only
# ignored by older versions, so it is not listed.
NEWER_FEATURES = {
    "## On Error": ("0.2.0b4", "0.2.0b3", "runs On Error steps as ordinary steps"),
    "## Finally": ("0.2.0b4", "0.2.0b3", "runs Finally steps as ordinary steps"),
    "inherit_config": ("0.2.0b4", "0.2.0b3", "ignores inherit_config"),
    "expressions in ${...}": ("0.3.0b1", "0.2.0b4", "turns expressions such as ${len(rows)} into empty text"),
    "and / or / not in conditions": ("0.3.0b1", "0.2.0b4", "reads and / or / not as part of a value"),
}


def _uses_expressions(steps: List[Step]) -> bool:
    for step in steps:
        for text in _placeholders([step.parameters, step.condition]):
            if not text.startswith("env.") and expressions.problem(text) is None:
                try:
                    if not expressions.is_plain_path(expressions.parse(text)):
                        return True
                except expressions.ExpressionError:
                    pass
    return False


def _uses_boolean_conditions(steps: List[Step]) -> bool:
    from .conditions import parse_boolean
    for step in steps:
        for condition in (step.condition, step.parameters.get("condition") if step.action == "logic.if" else None):
            if isinstance(condition, str) and parse_boolean(condition.strip().strip("`"))[0] != "is":
                return True
    return False


def _newer_features(flow: FlowDefinition) -> List[str]:
    used = []
    if flow.on_error_steps:
        used.append("## On Error")
    if flow.finally_steps:
        used.append("## Finally")
    steps = list(_walk(_all_steps(flow)))
    if any(s.action == "flow.call" and "inherit_config" in s.parameters for s in steps):
        used.append("inherit_config")
    if _uses_expressions(steps):
        used.append("expressions in ${...}")
    if _uses_boolean_conditions(steps):
        used.append("and / or / not in conditions")
    return used


def _version_problem(flow: FlowDefinition) -> Optional[str]:
    """The flow uses something an older Kinenix would run wrongly, and its `> Requires:` does not exclude that version."""
    used = _newer_features(flow)
    if not used:
        return None
    needed = max((NEWER_FEATURES[f][0] for f in used), key=version_key)
    allowed_old = [f for f in used if requirement_problem(flow.requires, version=NEWER_FEATURES[f][1]) is None]
    if not allowed_old:
        return None
    by_version = {}
    for feature in allowed_old:
        by_version.setdefault(NEWER_FEATURES[feature][1], []).append(NEWER_FEATURES[feature][2])
    effects = "; ".join(f"Kinenix {old} and older {' and '.join(what)}" for old, what in by_version.items())
    fix = "Add" if not flow.requires else "Raise"
    return (f"The flow uses {', '.join(allowed_old)}, which older workers would run wrongly: {effects}. "
            f"{fix} `> Requires: kinenix>={needed}` under the title, so older workers refuse the flow instead.")


def _placeholders(value: Any) -> Iterable[str]:
    """The text inside every ${...} of a parameter value, at any depth."""
    if isinstance(value, str):
        for match in VariableEvaluator.PATTERN.finditer(value):
            yield match.group(1).strip()
    elif isinstance(value, dict):
        for item in value.values():
            yield from _placeholders(item)
    elif isinstance(value, list):
        for item in value:
            yield from _placeholders(item)


def _expression_problems(step: Step, where: str) -> List[str]:
    """Expressions that cannot be read, or that call a function that does not exist (docs/design/expressions.md)."""
    found = []
    for text in _placeholders([step.parameters, step.condition]):
        problem = expressions.problem(text)
        if problem and problem not in found:
            found.append(problem)
    line = f", line {step.line}" if step.line else ""
    return [f"{where}{line}: {problem}" for problem in found]


def validate_flow(flow: FlowDefinition) -> List[str]:
    """Return human-readable problems found in the flow; an empty list means none."""
    issues: List[str] = []
    known_actions = ActionRegistry.list_actions()

    problem = requirement_problem(flow.requires)
    if problem:
        issues.append(problem)
    newer = _version_problem(flow)
    if newer:
        issues.append(newer)

    for step in _walk(_all_steps(flow)):
        where = f"Step '{step.id}' ({step.name})"
        issues.extend(_expression_problems(step, where))
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

"""Static checks on a flow before it runs: unknown actions and parameters that no action reads.

A misspelled parameter (for example `timout`) is otherwise ignored silently and the action falls back to
its default, which is hard to notice. These checks only report; callers decide whether to warn or stop.
"""
import difflib
from typing import Iterable, List

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

import time
from typing import Any, Dict

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


@register_action("logic.set_variable")
class SetVariableAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        name = parameters.get("name")
        value = parameters.get("value")
        if name:
            context.set_variable(name, value)
        return value


@register_action("logic.delay")
class DelayAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        seconds = float(parameters.get("seconds", 1.0))
        time.sleep(seconds)
        return {"delayed_seconds": seconds}


@register_action("logic.if")
class IfAction(BaseAction):
    """Conditional branching action. Handled with sub_steps by FlowInterpreter."""
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        return {"action": "logic.if"}


@register_action("logic.loop")
class LoopAction(BaseAction):
    """Loop iteration action. Handled with sub_steps by FlowInterpreter."""
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        return {"action": "logic.loop"}


@register_action("logic.append")
class AppendAction(BaseAction):
    """Appends an item to a list or datatable in context variables."""
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        target = parameters.get("target") or parameters.get("var_name") or parameters.get("list_var")
        item = parameters.get("item")
        if not target:
            raise ValueError("logic.append requires 'target' parameter specifying variable name")

        current = context.get_variable(target)
        if current is None:
            current = []
            context.set_variable(target, current)
        elif not isinstance(current, list):
            raise TypeError(f"Target variable '{target}' must be a list, got {type(current).__name__}")

        current.append(item)
        return {"target": target, "total_items": len(current), "appended": item}


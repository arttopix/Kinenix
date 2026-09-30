from typing import Any, Dict
from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext


class SubflowExecutionError(RuntimeError):
    """Raised when a child subflow execution fails with an unhandled error."""
    def __init__(self, message: str, subflow_name: str = "", failed_step_id: str = "", child_context: Any = None):
        super().__init__(message)
        self.subflow_name = subflow_name
        self.failed_step_id = failed_step_id
        self.child_context = child_context


@register_action("flow.call")
class FlowCallAction(BaseAction):
    """
    Executes an external child flow (subflow) within an isolated context.
    Main execution logic is handled by FlowInterpreter._handle_flow_call_step.
    """
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        return {"action": "flow.call"}


@register_action("flow.return")
class FlowReturnAction(BaseAction):
    """
    Outputs a structured return payload from a subflow and triggers early exit.
    Parameters:
      - value: Payload (dict, list, string, number, or primitive) to return to caller.
    """
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        value = parameters.get("value")
        context.set_variable("__return_value__", value)
        context.set_variable("__early_exit__", True)
        return {"returned": value}

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


class BusinessRuleError(RuntimeError):
    """A business exception: the data or situation breaks a rule. Recorded as error type Business and never retried."""


class FlowFailedError(RuntimeError):
    """A technical failure raised on purpose by flow.fail with category 'technical'."""


def is_business_error(exc: BaseException) -> bool:
    """Business exceptions are recognized by class name, so actions can define their own *Business* errors."""
    return "Business" in type(exc).__name__


@register_action("flow.fail")
class FlowFailAction(BaseAction):
    """
    Stops the flow with a clear message, typically under a condition, for example when expected data is missing.
    Parameters:
      - message: Text recorded as the error message and shown to whoever handles the failure.
      - category: 'business' (default, not retried) or 'technical'.
    """
    accepted_parameters = ('message', 'category')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        message = str(parameters.get("message") or "Flow stopped by flow.fail")
        category = str(parameters.get("category", "business")).lower()
        if category == "business":
            raise BusinessRuleError(message)
        if category == "technical":
            raise FlowFailedError(message)
        raise ValueError(f"flow.fail: category must be 'business' or 'technical', got '{category}'")


@register_action("flow.call")
class FlowCallAction(BaseAction):
    """
    Executes an external child flow (subflow) within an isolated context.
    Main execution logic is handled by FlowInterpreter._handle_flow_call_step.
    """
    accepted_parameters = ('flow', 'inputs', 'outputs', 'propagate_sessions')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        return {"action": "flow.call"}


@register_action("flow.return")
class FlowReturnAction(BaseAction):
    """
    Outputs a structured return payload from a subflow and triggers early exit.
    Parameters:
      - value: Payload (dict, list, string, number, or primitive) to return to caller.
    """
    accepted_parameters = ('value',)

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        value = parameters.get("value")
        context.set_variable("__return_value__", value)
        context.set_variable("__early_exit__", True)
        return {"returned": value}

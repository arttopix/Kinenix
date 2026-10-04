from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from ..models.context import ExecutionContext

# Parameters read by actions that find an element through _resolve_locator
LOCATOR_PARAMETERS: Tuple[str, ...] = ("selector", "label")


class BaseAction(ABC):
    """
    Abstract base class for all Kinenix Actions.
    """

    action_type: str = "base"

    # Parameter names this action reads. The flow validator reports any other name as a likely typo
    # (for example a misspelled key that would otherwise be ignored silently). None skips the check.
    accepted_parameters: Optional[Tuple[str, ...]] = None

    @abstractmethod
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        """
        Executes the action with given parameters and context.
        Returns output data to be stored or used by downstream steps.
        """
        pass

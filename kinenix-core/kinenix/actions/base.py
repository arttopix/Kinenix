from abc import ABC, abstractmethod
from typing import Any, Dict

from ..models.context import ExecutionContext


class BaseAction(ABC):
    """
    Abstract base class for all Kinenix Actions.
    """

    action_type: str = "base"

    @abstractmethod
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        """
        Executes the action with given parameters and context.
        Returns output data to be stored or used by downstream steps.
        """
        pass

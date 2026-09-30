from typing import Dict, Type
from .base import BaseAction


class ActionRegistry:
    """
    Registry mapping action string names (e.g. 'excel.read', 'logic.set_variable') to Action Classes.
    """

    _registry: Dict[str, Type[BaseAction]] = {}

    @classmethod
    def register(cls, action_type: str, action_class: Type[BaseAction]) -> None:
        cls._registry[action_type] = action_class

    @classmethod
    def get(cls, action_type: str) -> Type[BaseAction]:
        if action_type not in cls._registry:
            raise KeyError(f"Action '{action_type}' is not registered in ActionRegistry.")
        return cls._registry[action_type]

    @classmethod
    def list_actions(cls) -> Dict[str, Type[BaseAction]]:
        return dict(cls._registry)


def register_action(action_type: str):
    def decorator(cls: Type[BaseAction]):
        cls.action_type = action_type
        ActionRegistry.register(action_type, cls)
        return cls
    return decorator

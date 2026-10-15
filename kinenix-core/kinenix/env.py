"""Kinenix settings from the environment, with the names from before the rename to Hub and the saved settings file.

Old names still work, with a warning. Settings that `kinenix connect` and `kinenix hub setup` save in
~/.kinenix/kinenix.env (the Hub this machine sends runs to) are used when the environment has no value.
"""
import logging
import os
from typing import Set

logger = logging.getLogger("kinenix")

# New name -> name used before the rename
LEGACY_NAMES = {
    "KINENIX_HUB_URL": "KINENIX_ORCHESTRATOR_URL",
    "KINENIX_HUB_API_KEY": "KINENIX_ORCHESTRATOR_API_KEY",
}

_warned: Set[str] = set()


def get_env(name: str, default: str = "") -> str:
    """
    Value of `name` from the environment, else of its pre-rename name (warning once per name), else the
    value saved in ~/.kinenix/kinenix.env, else `default`.
    """
    value = os.environ.get(name)
    if value:
        return value
    old = LEGACY_NAMES.get(name)
    if old and os.environ.get(old):
        if old not in _warned:
            _warned.add(old)
            logger.warning(f"{old} is deprecated; rename it to {name}.")
        return os.environ[old]
    from .workspace import saved_settings  # imported here, so importing this module never reads the file
    return saved_settings().get(name) or default


def env_source(name: str) -> str:
    """Where get_env finds `name`: "environment", "saved", or "" when it is not set."""
    old = LEGACY_NAMES.get(name)
    if os.environ.get(name) or (old and os.environ.get(old)):
        return "environment"
    from .workspace import saved_settings
    return "saved" if saved_settings().get(name) else ""

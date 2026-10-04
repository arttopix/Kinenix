"""Environment variables renamed when the Orchestrator became the Hub: old names still work, with a warning."""
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
    """Value of `name`, else of its pre-rename name (warning once per name), else `default`."""
    value = os.environ.get(name)
    if value:
        return value
    old = LEGACY_NAMES.get(name)
    if old and os.environ.get(old):
        if old not in _warned:
            _warned.add(old)
            logger.warning(f"{old} is deprecated; rename it to {name}.")
        return os.environ[old]
    return default

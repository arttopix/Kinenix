"""`> Requires: kinenix>=0.2.0b4` in a flow.md: the Kinenix version a flow needs.

A worker that is too old refuses to run the flow with a clear message, instead of running steps it does not
understand (Kinenix 0.2.0b3 and older would run On Error steps as ordinary steps). Versions are compared
without extra dependencies; the forms Kinenix uses are 1.2.3, 1.2.3a1, 1.2.3b4, 1.2.3rc1, and 1.2.3.dev1.
"""
import operator
import re
from typing import Optional, Tuple

from .. import __version__  # read at call time, so tests can change it

_VERSION = re.compile(r"^v?(\d+(?:\.\d+)*)(?:(a|b|rc)(\d+))?(?:\.dev(\d+))?$", re.I)
# `kinenix>=0.2.0b4`, and further conditions after a comma: `kinenix>=0.2.0b4, <1.0`
_REQUIREMENT = re.compile(r"^\s*(?:kinenix\s*)?(>=|<=|==|!=|>|<)\s*(\S+)\s*$", re.I)
_OPERATORS = {">=": operator.ge, "<=": operator.le, "==": operator.eq, "!=": operator.ne,
              ">": operator.gt, "<": operator.lt}
_PRE_RELEASE = {"a": 0, "b": 1, "rc": 2}


def version_key(version: str) -> Optional[Tuple]:
    """A sortable key for a version, or None when it is not in a supported form."""
    match = _VERSION.match(version.strip())
    if not match:
        return None
    release = tuple(int(part) for part in match.group(1).split("."))
    release = release + (0,) * (4 - len(release))
    # A final release sorts after its pre-releases; a .dev release sorts before the same version without it
    pre = (_PRE_RELEASE[match.group(2).lower()], int(match.group(3))) if match.group(2) else (3, 0)
    dev = (0, int(match.group(4))) if match.group(4) else (1, 0)
    return release, pre, dev


def requirement_problem(requires: Optional[str], version: Optional[str] = None) -> Optional[str]:
    """None when this Kinenix (or `version`) satisfies `requires`, or nothing is required; otherwise what is wrong."""
    if not requires or not str(requires).strip():
        return None
    version = version or __version__
    parts = [part for part in str(requires).split(",") if part.strip()]
    current = version_key(version)
    for part in parts:
        match = _REQUIREMENT.match(part)
        wanted = version_key(match.group(2)) if match else None
        if not match or wanted is None:
            return (f"'> Requires: {requires}' is not understood. "
                    f"Write it as `> Requires: kinenix>=0.2.0b4`.")
        if current is not None and not _OPERATORS[match.group(1)](current, wanted):
            return (f"This flow requires {str(requires).strip()}, but this machine runs Kinenix {version}. "
                    f"Upgrade Kinenix here (pipx upgrade kinenix, or pip install -U kinenix) before running it.")
    return None

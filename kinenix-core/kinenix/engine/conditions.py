"""Condition expressions such as `${status} == ok`, `${note} is empty`, or `${word} in ${allowed}`.

The expression is split into operands and an operator before any variable is replaced, so a value that
contains an operator character (for example "< 5,000 km") can never split the expression in the wrong
place. Text inside ${...} and inside quotes is never read as an operator. No eval is used.
"""
import re
from typing import Any, Dict, Optional, Tuple

from .evaluator import VariableEvaluator

# Binary operators: symbol or words -> operator name understood by FlowInterpreter._evaluate_condition
_SYMBOL_OPERATORS = (("==", "equals"), ("!=", "not_equals"), (">=", "greater_than_or_equal"),
                     ("<=", "less_than_or_equal"), (">", "greater_than"), ("<", "less_than"))
_WORD_OPERATORS = re.compile(
    r"\s(?P<op>not\s+contains|not\s+in|contains|in|starts\s+with|ends\s+with)\s", re.IGNORECASE)
_EMPTY_CHECK = re.compile(r"\s+is\s+(?P<not>not\s+)?empty\s*$", re.IGNORECASE)
_WORD_NAMES = {"not contains": "not_contains", "not in": "not_in", "contains": "contains", "in": "in",
               "starts with": "starts_with", "ends with": "ends_with"}


def _mask(expression: str) -> str:
    """Hides ${...} placeholders and quoted text behind a filler of the same length."""
    out = list(expression)
    i = 0
    while i < len(expression):
        if expression.startswith("${", i):
            end = expression.find("}", i)
            end = len(expression) - 1 if end == -1 else end
            out[i:end + 1] = "\0" * (end + 1 - i)
            i = end + 1
        elif expression[i] in "'\"":
            end = expression.find(expression[i], i + 1)
            if end == -1:
                i += 1
                continue
            out[i:end + 1] = "\0" * (end + 1 - i)
            i = end + 1
        else:
            i += 1
    return "".join(out)


def split_condition(expression: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Splits `left OP right` into (left, operator name, right), using the leftmost operator outside
    placeholders and quotes; `left is empty` gives (left, "is_empty", None). None when there is no operator.
    """
    masked = _mask(expression)

    best = None  # (start, end, name)
    for symbol, name in _SYMBOL_OPERATORS:
        pos = masked.find(symbol)
        if pos != -1 and (best is None or pos < best[0] or (pos == best[0] and len(symbol) > best[1] - best[0])):
            best = (pos, pos + len(symbol), name)
    word = _WORD_OPERATORS.search(masked)
    if word and (best is None or word.start("op") < best[0]):
        best = (word.start("op"), word.end("op"), _WORD_NAMES[" ".join(word.group("op").lower().split())])

    empty = _EMPTY_CHECK.search(masked)
    if empty and (best is None or best[0] >= empty.start()):
        return expression[:empty.start()], "is_not_empty" if empty.group("not") else "is_empty", None
    if best is None:
        return None
    return expression[:best[0]], best[2], expression[best[1]:]


def _operand(raw: str, variables: Dict[str, Any]) -> Any:
    """A side of a condition: quoted text stays text (with ${...} replaced inside), anything else is evaluated."""
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"`":
        return str(VariableEvaluator.evaluate_value(text[1:-1], variables))
    return VariableEvaluator.evaluate_value(text, variables)


def resolve_condition(expression: Any, variables: Dict[str, Any]) -> Tuple[Any, Optional[str], Any]:
    """
    Turns a condition into (left value, operator name, right value). The operator is None when the
    expression has none; left is then the evaluated expression, read as true or false by the caller.
    """
    if isinstance(expression, bool):
        return expression, None, None
    text = str(expression).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    parts = split_condition(text)
    if parts is None:
        return VariableEvaluator.evaluate_value(text, variables), None, None
    left, op, right = parts
    return _operand(left, variables), op, (None if right is None else _operand(right, variables))


# ---------------------------------------------------------------------------------------------------
# and / or / not (docs/design/expressions.md, section 6)
# ---------------------------------------------------------------------------------------------------

_NOT_PREFIX = re.compile(r"^\s*not\s+", re.IGNORECASE)
_PLACEHOLDER_ONLY = re.compile(r"^\s*`?\$\{[^}]+\}`?\s*$")


def _split_top(text: str, word: str) -> list:
    """Splits at ` word ` outside ${...} and quotes (any case)."""
    masked = _mask(text)
    pattern = re.compile(rf"\s+{word}\s+", re.IGNORECASE)
    parts, start = [], 0
    for match in pattern.finditer(masked):
        parts.append(text[start:match.start()])
        start = match.end()
    parts.append(text[start:])
    return parts


def _is_comparison(text: str) -> bool:
    """A part that can stand alone as a condition: it has an operator, or is a single ${...}."""
    inner = _NOT_PREFIX.sub("", text, count=1)
    return bool(inner.strip()) and (split_condition(inner.strip()) is not None or bool(_PLACEHOLDER_ONLY.match(inner)))


def _is_conjunction(text: str) -> bool:
    parts = _split_top(text, "and")
    return all(_is_comparison(p) for p in parts)


def parse_boolean(expression: str) -> Any:
    """
    The structure of a condition: ("or", [...]), ("and", [...]), ("not", text), or ("is", text).
    A condition is split at and / or only when every part is a condition by itself, so a value such as
    `Johnson and Johnson` is never split. `and` binds tighter than `or`.
    """
    text = expression.strip()
    ors = _split_top(text, "or")
    if len(ors) > 1 and all(_is_conjunction(p) for p in ors):
        return ("or", [_parse_conjunction(p) for p in ors])
    return _parse_conjunction(text)


def _parse_conjunction(text: str) -> Any:
    ands = _split_top(text, "and")
    if len(ands) > 1 and all(_is_comparison(p) for p in ands):
        return ("and", [_parse_atom(p) for p in ands])
    return _parse_atom(text)


def _parse_atom(text: str) -> Any:
    stripped = text.strip()
    negated = _NOT_PREFIX.match(stripped)
    if negated and _is_comparison(stripped[negated.end():]):
        return ("not", stripped[negated.end():].strip())
    return ("is", stripped)

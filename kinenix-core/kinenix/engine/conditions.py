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

"""Expressions inside ${...}: functions, arithmetic, and indexing, without eval (docs/design/expressions.md).

The text is parsed with ast.parse, which only builds a syntax tree and runs nothing. The tree is then
checked against a short list of allowed node types and functions, and walked by the evaluator below.
Nothing here calls eval, exec, or compile, and only dictionary keys are read: attributes of Python
objects and names starting with "_" are refused.
"""
import ast
import math
import os
import re
import warnings
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple

MAX_LENGTH = 500
MAX_DEPTH = 20

# Text that cannot be read, or is refused, is an error only when it clearly means an expression: a function
# call, brackets, quotes, or an operator other than "-". Otherwise it is a key name that is missing, such as
# "row.Unit Price (THB)", "row.Terms and Conditions", or "row.Order-ID", and gives empty as before.
_LOOKS_LIKE_EXPRESSION = re.compile(r"\w\(|\[|['\"]|[+*/%<>=!]")
_PLAIN_NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")
# The first number in a text: optional minus or opening parenthesis, digits with thousands separators, decimals
# A minus sign or "(" counts only when no letter or digit is right before it: "INV-100" is 100, "(1,200)" is -1200
_NUMBER_IN_TEXT = re.compile(r"(?:(?<!\w)(?P<neg>[-(]))?\s*(?P<num>\d[\d,]*(?:\.\d+)?)")


class ExpressionError(ValueError):
    """An expression that cannot be read or evaluated; the message names the expression and the reason."""

    def __init__(self, expression: str, reason: str):
        self.expression = expression
        self.reason = reason
        super().__init__(f"${{{expression}}}: {reason}")


class ExpressionSyntaxError(ExpressionError):
    """The text cannot be read as an expression at all (as opposed to an expression that is refused)."""


class _Environment:
    """`env` inside an expression: `env.NAME` reads an environment variable, as `${env.NAME}` does."""

    def get(self, name: str) -> str:
        return os.getenv(name, "")


# ---------------------------------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------------------------------

def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _whole(value: Any) -> Any:
    """A float that is a whole number is shown without .0."""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return int(value)
    return value


def _number(value: Any, what: str) -> Any:
    """A number for arithmetic: numbers, and text that is a plain number such as "12" or "3.5"."""
    if isinstance(value, bool):
        raise ValueError(f"{what} is true or false, not a number")
    if isinstance(value, (int, float)):
        return value
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{what} is empty")
    if isinstance(value, str) and _PLAIN_NUMBER.match(value.strip()):
        text = value.strip()
        return float(text) if "." in text else int(text)
    raise ValueError(f"{what} '{_text(value)[:50]}' is not a number; use number(...) to read a number from text")


def _whole_number(value: Any, what: str) -> int:
    number = _number(value, what)
    if isinstance(number, float) and not number.is_integer():
        raise ValueError(f"{what} must be a whole number, not {number}")
    return int(number)


# ---------------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------------

def _len(x: Any) -> int:
    if x is None:
        return 0
    if isinstance(x, (str, list, tuple, dict)):
        return len(x)
    return len(_text(x))


def _join(items: Any, sep: Any = ", ") -> str:
    if items is None:
        return ""
    if isinstance(items, str):
        return items
    if isinstance(items, (list, tuple)):
        return _text(sep).join(_text(item) for item in items)
    raise ValueError("join needs a list")


def _parse_number(x: Any) -> Any:
    if x is None or (isinstance(x, str) and not x.strip()):
        return None
    if isinstance(x, bool):
        raise ValueError("number needs text or a number, not true or false")
    if isinstance(x, (int, float)):
        return x
    text = _text(x)
    match = _NUMBER_IN_TEXT.search(text)
    if not match:
        raise ValueError(f"'{text[:50]}' contains no number")
    digits = match.group("num").replace(",", "")
    value = float(digits) if "." in digits else int(digits)
    return -value if match.group("neg") else value


def _trim(x: Any) -> str:
    return _text(x).strip()


def _lower(x: Any) -> str:
    return _text(x).lower()


def _upper(x: Any) -> str:
    return _text(x).upper()


def _replace(x: Any, old: Any, new: Any) -> str:
    old_text = _text(old)
    if not old_text:
        raise ValueError("replace needs a non-empty text to replace")
    return _text(x).replace(old_text, _text(new))


def _default(x: Any, fallback: Any) -> Any:
    return fallback if x is None or x == "" else x


def _round(x: Any, digits: Any = 0) -> Any:
    if x is None or x == "":
        return None
    places = _whole_number(digits, "the number of digits")
    result = round(_number(x, "the value"), places)
    return int(result) if places <= 0 else result


def _part(x: Any, sep: Any, n: Any) -> str:
    separator = _text(sep)
    if not separator:
        raise ValueError("part needs a non-empty separator")
    pieces = _text(x).split(separator)
    index = _whole_number(n, "the piece number")
    if -len(pieces) <= index < len(pieces):
        return pieces[index]
    return ""


def _substring(x: Any, start: Any, length: Any = None) -> str:
    text = _text(x)
    first = _whole_number(start, "the start")
    if first < 0:
        raise ValueError("the start is counted from 0 and cannot be negative")
    if length is None:
        return text[first:]
    count = _whole_number(length, "the length")
    if count < 0:
        raise ValueError("the length cannot be negative")
    return text[first:first + count]


# name -> (function, fewest arguments, most arguments)
FUNCTIONS: Dict[str, Tuple[Callable[..., Any], int, int]] = {
    "len": (_len, 1, 1),
    "join": (_join, 1, 2),
    "number": (_parse_number, 1, 1),
    "trim": (_trim, 1, 1),
    "lower": (_lower, 1, 1),
    "upper": (_upper, 1, 1),
    "replace": (_replace, 3, 3),
    "default": (_default, 2, 2),
    "round": (_round, 1, 2),
    "part": (_part, 3, 3),
    "substring": (_substring, 2, 3),
}

_OPERATORS: Dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
}
_SYMBOLS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%"}


# ---------------------------------------------------------------------------------------------------
# Parsing and checking
# ---------------------------------------------------------------------------------------------------

_REFUSED = {
    ast.Compare: "comparisons belong in a condition, for example `${a} > ${b}`",
    ast.BoolOp: "and / or belong in a condition, for example `${a} == x and ${b} == y`",
    ast.Lambda: "lambdas are not allowed",
    ast.ListComp: "comprehensions are not allowed",
    ast.SetComp: "comprehensions are not allowed",
    ast.DictComp: "comprehensions are not allowed",
    ast.GeneratorExp: "comprehensions are not allowed",
    ast.JoinedStr: "f-strings are not allowed; write ${...} for each value",
    ast.IfExp: "if / else is not allowed; use a condition on the step",
    ast.NamedExpr: "assignment is not allowed",
    ast.Await: "await is not allowed",
    ast.Starred: "* in arguments is not allowed",
}


def _check(node: ast.AST, text: str, depth: int = 0) -> None:
    """Refuses everything outside the allowed node types and functions."""
    if depth > MAX_DEPTH:
        raise ExpressionError(text, f"nested more than {MAX_DEPTH} levels deep")
    if isinstance(node, ast.Expression):
        _check(node.body, text, depth + 1)
    elif isinstance(node, ast.Constant):
        if node.value is not None and not isinstance(node.value, (str, int, float, bool)):
            raise ExpressionError(text, f"the value {node.value!r} is not allowed")
    elif isinstance(node, ast.Name):
        if node.id.startswith("_"):
            raise ExpressionError(text, f"the name '{node.id}' is not allowed (names starting with _ are internal)")
    elif isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            raise ExpressionError(text, f"'.{node.attr}' is not allowed (names starting with _ are internal)")
        _check(node.value, text, depth + 1)
    elif isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            raise ExpressionError(text, "slices such as [1:3] are not allowed; use substring(...)")
        _check(node.value, text, depth + 1)
        _check(node.slice, text, depth + 1)
    elif isinstance(node, ast.BinOp):
        if type(node.op) not in _OPERATORS:
            raise ExpressionError(text, "only + - * / % are allowed")
        _check(node.left, text, depth + 1)
        _check(node.right, text, depth + 1)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.USub, ast.UAdd)):
            raise ExpressionError(text, "not belongs in a condition, for example `not ${a} is empty`")
        _check(node.operand, text, depth + 1)
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ExpressionError(text, "only functions can be called, not methods such as x.upper(); use upper(x)")
        name = node.func.id
        if name not in FUNCTIONS:
            raise ExpressionError(text, f"unknown function '{name}'; available: {', '.join(sorted(FUNCTIONS))}")
        if node.keywords:
            raise ExpressionError(text, f"{name} takes its values in order, without names")
        _, fewest, most = FUNCTIONS[name]
        if not fewest <= len(node.args) <= most:
            wanted = str(fewest) if fewest == most else f"{fewest} to {most}"
            raise ExpressionError(text, f"{name} takes {wanted} value{'s' if most > 1 else ''}, got {len(node.args)}")
        for arg in node.args:
            _check(arg, text, depth + 1)
    else:
        reason = next((why for kind, why in _REFUSED.items() if isinstance(node, kind)), None)
        raise ExpressionError(text, reason or f"{type(node).__name__} is not allowed")


@lru_cache(maxsize=2048)
def _syntax(text: str) -> ast.Expression:
    """The syntax tree, not checked yet. Raises ExpressionSyntaxError."""
    if len(text) > MAX_LENGTH:
        raise ExpressionSyntaxError(text[:40] + "...", f"longer than {MAX_LENGTH} characters")
    if "${" in text:
        raise ExpressionSyntaxError(text, "write variables without ${...} inside an expression, for example ${len(rows)}")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Python warns about some malformed text, such as "1if"
            tree = ast.parse(text.strip(), mode="eval")
    except SyntaxError as e:
        raise ExpressionSyntaxError(text, f"cannot be read ({e.msg})")
    except (ValueError, RecursionError, MemoryError) as e:
        raise ExpressionSyntaxError(text, f"cannot be read ({e.__class__.__name__})")
    return tree


@lru_cache(maxsize=2048)
def parse(text: str) -> ast.Expression:
    """The checked syntax tree of an expression. Raises ExpressionError."""
    tree = _syntax(text)
    _check(tree, text)
    return tree


def _means_expression(text: str) -> bool:
    return bool(_LOOKS_LIKE_EXPRESSION.search(text)) or "${" in text


def is_plain_path(tree: ast.Expression) -> bool:
    """True for a lookup such as `row.name`: names and dots only."""
    node = tree.body
    while isinstance(node, ast.Attribute):
        node = node.value
    return isinstance(node, ast.Name)


# ---------------------------------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------------------------------

def _evaluate(node: ast.AST, variables: Dict[str, Any], text: str) -> Any:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, variables, text)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id == "env" and "env" not in variables:
            return _Environment()
        return variables.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _evaluate(node.value, variables, text)
        if isinstance(base, (dict, _Environment)):
            return base.get(node.attr)
        return None  # only dictionary keys are read; never attributes of Python objects
    if isinstance(node, ast.Subscript):
        base = _evaluate(node.value, variables, text)
        key = _evaluate(node.slice, variables, text)
        if isinstance(base, dict):
            return base.get(key) if isinstance(key, (str, int, float)) else None
        if isinstance(base, (list, tuple, str)):
            index = _whole_number(key, "the index")
            return base[index] if -len(base) <= index < len(base) else None
        return None
    if isinstance(node, ast.BinOp):
        symbol = _SYMBOLS[type(node.op)]
        left = _number(_evaluate(node.left, variables, text), f"the value before {symbol}")
        right = _number(_evaluate(node.right, variables, text), f"the value after {symbol}")
        if isinstance(node.op, (ast.Div, ast.Mod)) and right == 0:
            raise ValueError("division by zero")
        result = _OPERATORS[type(node.op)](left, right)
        if isinstance(result, float) and not math.isfinite(result):
            raise ValueError("the result is too large")
        return _whole(result)
    if isinstance(node, ast.UnaryOp):
        value = _number(_evaluate(node.operand, variables, text), "the value")
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Call):
        function = FUNCTIONS[node.func.id][0]
        args: List[Any] = [_evaluate(arg, variables, text) for arg in node.args]
        return _whole(function(*args))
    raise ExpressionError(text, f"{type(node).__name__} is not allowed")  # _check refuses these first


def evaluate(text: str, variables: Dict[str, Any]) -> Any:
    """The value of an expression. Raises ExpressionError for every problem, and nothing else."""
    tree = parse(text)
    try:
        return _evaluate(tree, variables, text)
    except ExpressionError:
        raise
    except Exception as e:  # a wrong type or value in a function or operator
        raise ExpressionError(text, str(e) or e.__class__.__name__)


def evaluate_unresolved(text: str, variables: Dict[str, Any]) -> Any:
    """
    For text inside ${...} that is not a variable that exists (docs/design/expressions.md, section 4):
    an expression gives its value; a missing lookup gives empty, as before expressions existed.
    """
    try:
        tree = _syntax(text)
    except ExpressionSyntaxError:
        if _means_expression(text):
            raise
        return None
    if is_plain_path(tree):
        return None
    try:
        parse(text)
    except ExpressionError:
        if _means_expression(text):
            raise
        return None
    return evaluate(text, variables)


def problem(text: str) -> Optional[str]:
    """For `kinenix validate`: why this ${...} text cannot be evaluated, or None when it can (or is a lookup)."""
    if text.startswith("env."):
        return None
    try:
        tree = _syntax(text)
        if not is_plain_path(tree):
            parse(text)
    except ExpressionError as e:
        return str(e) if _means_expression(text) else None
    return None

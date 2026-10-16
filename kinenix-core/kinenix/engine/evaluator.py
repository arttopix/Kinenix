import os
import re
from typing import Any, Dict, Tuple

from . import expressions


class VariableEvaluator:
    """
    Evaluates ${...} in values: a variable such as ${row.Name} or ${env.HOME}, or an expression such as
    ${len(rows)} or ${number(row.price) * 2} (docs/design/expressions.md).

    A variable that exists is always read as before; the text is evaluated as an expression only when it
    names no existing variable. So keys such as "First Name" or "Role in Company" keep working.
    """

    PATTERN = re.compile(r"\$\{([^}]+)\}")

    @classmethod
    def evaluate_value(cls, value: Any, context_vars: Dict[str, Any]) -> Any:
        if isinstance(value, str):
            match = cls.PATTERN.fullmatch(value.strip())
            if match:
                var_expr = match.group(1).strip()
                return cls._resolve_expr(var_expr, context_vars)

            def replace_match(m):
                resolved = cls._resolve_expr(m.group(1).strip(), context_vars)
                return str(resolved) if resolved is not None else ""

            return cls.PATTERN.sub(replace_match, value)

        elif isinstance(value, dict):
            return {k: cls.evaluate_value(v, context_vars) for k, v in value.items()}
        elif isinstance(value, list):
            return [cls.evaluate_value(v, context_vars) for v in value]
        else:
            return value

    @classmethod
    def _resolve_expr(cls, expr: str, context_vars: Dict[str, Any]) -> Any:
        if expr.startswith("env."):
            env_key = expr[4:]
            return os.getenv(env_key, "")

        found, value = cls._lookup(expr, context_vars)
        if found:
            return value
        return expressions.evaluate_unresolved(expr, context_vars)

    @staticmethod
    def _lookup(expr: str, context_vars: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        (True, value) when the dotted path names an existing variable and every key on the way exists.
        Only dictionary keys are followed: attributes of Python objects are never read.
        """
        parts = expr.split(".")
        if parts[0] not in context_vars:
            return False, None
        current = context_vars[parts[0]]
        for part in parts[1:]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False, None
        return True, current

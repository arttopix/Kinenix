import os
import re
from typing import Any, Dict


class VariableEvaluator:
    """
    Evaluates variable expressions in string formats such as ${var_name} or ${env.ENV_VAR}.
    Also handles dictionary key traversal like ${row.Name}.
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

        parts = expr.split(".")
        root_key = parts[0]

        if root_key not in context_vars:
            return None

        current = context_vars[root_key]
        for part in parts[1:]:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        return current

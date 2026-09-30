# Action Documentation & Extension Standards

This document establishes the mandatory requirements for implementing, updating, and documenting standard actions within the **Kinenix** project.

---

## 1. Action Creation & Extension Protocol

Whenever a developer or AI assistant adds a new action or modifies an existing action in `kinenix-core/kinenix/actions/`:

1. **Inheritance & Registration:**
   - Every action must inherit from `BaseAction` (`kinenix.actions.base`).
   - The action class must be decorated with `@register_action("<category>.<action_name>")` from `kinenix.actions.registry`.
   - The module must be imported in `kinenix-core/kinenix/actions/__init__.py`.

2. **Parameter Validation & Typing:**
   - Define a dedicated Pydantic model (`BaseModel`) representing input parameters.
   - Enforce explicit type hints for all fields and default values where appropriate.

3. **Mandatory Documentation Update:**
   - `docs/actions_reference.md` **MUST** be updated in the same changeset or pull request.
   - Any new action must be included in the Table of Contents and categorized under the appropriate heading.

4. **Unit Test Coverage:**
   - A dedicated unit test verifying positive execution, parameter validation, and error scenarios must be created in `kinenix-core/tests/actions/` before merging.

---

## 2. Action Reference Documentation Format (Dual-Representation)

Every action documented in `docs/actions_reference.md` must follow the exact structure below, providing both the authoring Markdown format and the compiled JSON runtime schema:

```markdown
### `category.action_name`
[Brief description of what the action does and its underlying technology]

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `param_1` | string | Yes | - | Purpose of param_1 |
| `param_2` | boolean | No | `false` | Purpose of param_2 |

**Example in `flow.md` (Markdown):**
```markdown
### 1. Step Name (`category.action_name`)
- **param_1:** example_value
- **param_2:** false
```

**Compiled `flow.json`:**
```json
{
  "id": "step_1",
  "name": "Step Name",
  "action": "category.action_name",
  "parameters": {
    "param_1": "example_value",
    "param_2": false
  }
}
```
```

---

## 3. Formatting Rules & Constraints

- **Dual-Representation Mandatory:** Never provide JSON-only examples in `docs/actions_reference.md`. Always present the `flow.md` representation first, followed by the compiled runtime `flow.json`.
- **Markdown Specification Compliance:** Markdown examples must strictly follow `docs/flow_markdown_spec.md`:
  - Level 3 heading `### <id/number>. <Name> (<category.action_name>)` with registered action name in parentheses.
  - Parameters formatted as `- **<param_name>:** <value>`.
  - Nested sub-steps (`sub_steps`, `else_steps`) must follow standard indentation under `- **Sub-steps:**` and `- **Else-steps:**`.
- **No Emojis Policy:** Do not use emojis in documentation, rules, code, or logs.


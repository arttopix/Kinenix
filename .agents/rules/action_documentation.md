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
   - Declare every parameter name the action reads in `accepted_parameters` (use `LOCATOR_PARAMETERS + (...)` for actions that find an element). The flow validator and the tests depend on it: a test fails when an action has no declaration or when `docs/actions_reference.md` documents a parameter that is not declared.
   - Target architecture: a dedicated Pydantic model (`BaseModel`) per action with explicit types and defaults (see `AGENTS.md`, Current State vs. Target Architecture).

3. **Mandatory Documentation Update:**
   - `docs/actions_reference.md` **MUST** be updated in the same changeset or pull request.
   - Any new action must be included in the Table of Contents and categorized under the appropriate heading.

4. **Unit Test Coverage:**
   - A dedicated unit test verifying positive execution, parameter validation, and error scenarios must be created in `kinenix-core/tests/actions/` before merging.

---

## 2. Action Reference Documentation Format (Dual-Representation)

Every action documented in `docs/actions_reference.md` must follow the structure below, with a `flow.md` example:

```markdown
### `category.action_name`
[Brief description of what the action does and its underlying technology]

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `param_1` | string | Yes | - | Purpose of param_1 |
| `param_2` | boolean | No | `false` | Purpose of param_2 |

**Example:**
```markdown
### 1. Step Name (`category.action_name`)
- **param_1:** example_value
- **param_2:** false
```

**Output Format:** (when the action returns a structured value)
```json
{"status": "done"}
```
```

---

## 3. Formatting Rules & Constraints

- **`flow.md` only:** Flows exist only as `flow.md`, so examples show `flow.md`. Do not add compiled `flow.json` examples. `kinenix-core/tests/test_doc_examples.py` compiles and validates every `flow.md` example in `docs/`.
- **Markdown Specification Compliance:** Markdown examples must strictly follow `docs/flow_markdown_spec.md`:
  - Level 3 heading `### <id/number>. <Name> (<category.action_name>)` with registered action name in parentheses.
  - Parameters formatted as `- **<param_name>:** <value>`.
  - Nested sub-steps (`sub_steps`, `else_steps`) must follow standard indentation under `- **Sub-steps:**` and `- **Else-steps:**`.
- **No Emojis Policy:** Do not use emojis in documentation, rules, code, or logs.


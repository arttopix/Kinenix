# Coding Standards & Module Guidelines

This document defines code conventions, typing standards, and module implementation patterns for the **BAT Automate** project.

---

## 1. General Rules

- **No Emojis:** Do not include emojis or emotional icons in code, comments, commit messages, documentation, or generated files.
- **Documentation Requirement:** Every module must have complete setup, configuration, and execution instructions in its respective `README.md`.
- **Standard CLI Commands:** Any CLI tool provided by a module must support the standard commands:
  - `version`: Display version information, Python runtime, and host OS.
  - `list`: Enumerate available flows or targets.
  - `run <flow>`: Execute a targeted flow using the smart resolver.

---

## 2. Python Standards (`bat-core`)

- **Runtime Target:** Python 3.10 or higher.
- **Type Annotations:** All function signatures and class definitions must include full type hints.
- **Data Models:** Use Pydantic models for data validation, serialization, and flow schema representations.
- **Action Implementation:**
  - Every action must inherit from `BaseAction`.
  - Actions must define a unique `name` and a Pydantic `schema` for input parameter validation.
  - Keep action implementations focused, modular, and cleanly decoupled from GUI dependencies.
  - Whenever an action is added or updated, `docs/actions_reference.md` must be updated with dual-representation examples (Markdown and JSON). See `.agents/rules/action_documentation.md`.
- **Variable Evaluation:**
  - Variable references syntax: `${variable_name}`.
  - Evaluation must remain secure without using arbitrary `eval()` or unvalidated code execution.

---

## 3. Frontend Standards (`bat-studio` & Dashboard)

- **Framework:** Tauri + React + TypeScript.
- **Canvas Components:** Build canvas nodes and edges using standard React components to allow code reuse between Desktop Studio and the Web Orchestrator.
- **Multi-Layer Selectors:** UI recorder and inspector must generate resilient multi-layer selectors (XPath, ID, Text, CSS) rather than brittle single-point selectors.

---

## 4. API & Backend Standards (`bat-orchestrator`)

- **Framework:** FastAPI with asynchronous endpoint handlers.
- **Notification Priority:** Notifications must support LINE Messaging API first, followed by Microsoft Teams and Email.
- **Stateless Handlers:** Background task processing must be routed through Redis and Celery/task queues.

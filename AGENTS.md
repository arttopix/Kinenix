# AGENTS.md

Entry point for AI coding assistants (any vendor) working on **Kinenix**, a local AI-native RPA framework in Python. Read this file first, then open the rule or doc files relevant to your task. Detailed rules live in `.agents/rules/`; this file does not duplicate them.

## Repository Map

| Path | What it is | State |
| :--- | :--- | :--- |
| `kinenix-core/` | Flow interpreter, variable evaluator, action plugins, `kinenix` CLI | Implemented |
| `kinenix-worker/` | Unattended runner with schedule and file-watch triggers | Implemented |
| `kinenix-studio/` | FastAPI server + React/Vite web UI for viewing and editing flows | Implemented (web, not Tauri yet) |
| `kinenix-orchestrator/` | FastAPI + SQLAlchemy telemetry receiver and dashboard | Early (HTTP push, SQLite default) |
| `flows/` | Project bundles (`flow.json`, `flow.md`, `config/`, `assets/`, `subflows/`); `@shared/` holds reusable subflows | |
| `schemas/` | JSON schemas for flows and execution logs | |
| `docs/` | Human and AI reference documentation | |
| `.agents/rules/` | Detailed engineering rules | |

Key code locations:
- Interpreter and retry/fallback logic: `kinenix-core/kinenix/engine/interpreter.py`
- `${var}` expression resolution (no `eval`): `kinenix-core/kinenix/engine/evaluator.py`
- `flow.md` to `flow.json` compiler: `kinenix-core/kinenix/engine/markdown.py`
- Action base class and registry: `kinenix-core/kinenix/actions/base.py`, `registry.py`
- Orchestrator auth (worker API key, dashboard Basic Auth): `kinenix-orchestrator/kinenix_orchestrator/security.py`

## Setup and Commands

The project uses a virtual environment at `.venv/` in the repository root. On Windows, the interpreter is `.venv/Scripts/python.exe`; the system Python does not have the dependencies installed.

```powershell
# Install (editable)
.venv/Scripts/python.exe -m pip install -e "kinenix-core[dev]" -e "kinenix-worker[dev]" -e "kinenix-studio[dev]" -e "kinenix-orchestrator[dev]"

# Tests: run kinenix-core from its own directory, the others from the repo root
cd kinenix-core; ../.venv/Scripts/python.exe -m pytest -q; cd ..
.venv/Scripts/python.exe -m pytest -q kinenix-worker/tests
.venv/Scripts/python.exe -m pytest -q kinenix-studio/tests
.venv/Scripts/python.exe -m pytest -q kinenix-orchestrator/tests

# Studio frontend
cd kinenix-studio/frontend; npm ci; npm run build

# Run a flow / start the orchestrator
kinenix run flows/examples/rpachallenge
kinenix orchestrator --port 8080
```

Run the test suites for every module you touch before reporting work as done. GitHub Actions (`.github/workflows/ci.yml`) runs the same commands on every push and pull request to `main` and `dev`; keep the workflow in sync when these commands change.

## Rules Index

Read the matching file before working in that area:

| Task | Read |
| :--- | :--- |
| Adding or changing an action | `.agents/rules/action_documentation.md`, `docs/actions_reference.md` |
| Writing or compiling flows | `docs/flow_markdown_spec.md`, `docs/project_bundles.md`, `schemas/flow.schema.json` |
| Errors, retries, failure telemetry | `.agents/rules/error_handling.md` |
| Logs and telemetry format | `.agents/rules/logging.md`, `docs/logging.md` |
| Secrets, credentials, data privacy | `.agents/rules/security.md` |
| Orchestrator setup and API keys | `docs/orchestrator.md` |
| Code style | `.agents/rules/coding_standards.md` |
| Tests | `.agents/rules/testing_standards.md` |
| Commits and branches | `.agents/rules/git_workflow.md` |
| Module boundaries and design principles | `.agents/rules/architecture.md`, `docs/architecture.md` |
| What is built vs. planned, next priorities | `docs/roadmap.md` |
| Finding any other document | `docs/README.md` |

## Non-Negotiable Rules

1. **Never commit or push without an explicit instruction from the user.** Finish the work, summarize it, and wait. (`collaboration.md`, `git_workflow.md`)
2. **Present a plan before large changes.** (`collaboration.md`)
3. **No secrets in code, `flow.json`, or `config.json`.** Read them from environment variables. (`security.md`)
4. **No `eval()` or arbitrary code execution** when evaluating flow expressions.
5. **Update `docs/actions_reference.md` in the same change** whenever an action is added or modified, with both `flow.md` and `flow.json` examples.
6. **No emojis anywhere:** code, comments, UI text, commits, pull requests, issues, release notes, and documentation.
7. **Keep business data local.** Do not send flow data to third-party cloud APIs unless an action is explicitly designed for it.
8. **Use Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, ...).
9. **No AI attribution trailers in commits** (no `Co-Authored-By` for AI assistants). AI help is credited in the README. Pull request descriptions may end with the plain line `Generated with Claude Code`. (`git_workflow.md`)

## Current State vs. Target Architecture

Some rule files and the README describe the target architecture, not what exists today. Follow the existing code for anything listed below, and ask before introducing the target technology.

| Topic | Target (in rules/README) | Current code |
| :--- | :--- | :--- |
| Action parameters | Pydantic model per action | Actions receive a plain `Dict[str, Any]` |
| Action tests | `kinenix-core/tests/actions/` | Tests live directly in `kinenix-core/tests/` |
| Studio | Tauri desktop app | FastAPI + React/Vite in the browser |
| Orchestrator backend | Async handlers, PostgreSQL, Redis/Celery | Sync handlers, SQLite by default, no queue |
| Worker communication | WebSocket job dispatch and log streaming | Workers push telemetry over HTTP; no dispatch |

When you change code so that it matches a target, update this table and `docs/roadmap.md`.

## Environment Variables

| Variable | Used by | Purpose |
| :--- | :--- | :--- |
| `KINENIX_ORCHESTRATOR_URL` | kinenix-core | Orchestrator URL for telemetry upload |
| `KINENIX_ORCHESTRATOR_API_KEY` | kinenix-core | API key sent as `X-API-Key` |
| `KINENIX_WORKER_ID` | kinenix-core | Worker identifier in telemetry |
| `ORCHESTRATOR_API_KEY` | kinenix-orchestrator | Required key for write endpoints; unset means localhost-only |
| `ORCHESTRATOR_DASHBOARD_USER` / `ORCHESTRATOR_DASHBOARD_PASSWORD` | kinenix-orchestrator | Basic Auth for the dashboard and read endpoints; unset password means localhost-only |
| `ORCHESTRATOR_HOST` / `ORCHESTRATOR_PORT` | kinenix-orchestrator | Bind address (default `127.0.0.1`, localhost only) and port |
| `DATABASE_URL` | kinenix-orchestrator | SQLAlchemy connection string |
| `CENTRAL_LLM_URL` | kinenix-orchestrator | LLM endpoint for failure analysis |

## Keeping This File Accurate

This file is read by AI tools as ground truth. If you change a command, path, module state, or rule referenced here, update it in the same change. Keep it short: put details in `docs/` or `.agents/rules/` and link to them.

Documentation layout: each topic has one owning file (index in `docs/README.md`). `docs/` describes how the system works; `.agents/rules/` states only what must or must not be done. Link between them instead of copying content.

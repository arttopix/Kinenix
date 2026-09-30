# .agents/

Engineering rules for AI coding assistants working on BAT Automate. Antigravity IDE auto-loads every file in `.agents/rules/`; other tools reach these rules through [AGENTS.md](../AGENTS.md) at the repository root, which is the main entry point.

This directory is for AI developer tooling only. It is unrelated to `bat-worker`, the runtime robot daemon.

## Rules

| File | Scope |
| :--- | :--- |
| `rules/architecture.md` | Design principles and module boundaries that code must respect |
| `rules/coding_standards.md` | Python typing, `BaseAction` pattern, `${var}` evaluation, CLI conventions, no emojis |
| `rules/action_documentation.md` | Required documentation for every action (`flow.md` + `flow.json` examples) |
| `rules/error_handling.md` | Technical vs. business exceptions and failure telemetry |
| `rules/logging.md` | Execution log requirements, variable sanitization, business metrics |
| `rules/security.md` | Secrets, log masking, local data privacy |
| `rules/testing_standards.md` | pytest conventions and benchmark regression checks |
| `rules/git_workflow.md` | Conventional Commits, branch naming, no autonomous commit or push |
| `rules/collaboration.md` | Plan before large changes, command safety, keeping docs current |

Rules state what must or must not be done. Descriptions of how the system works belong in [docs/](../docs/README.md); link to them instead of copying.

# Documentation Index

Each topic has one owning document. Other files link here instead of repeating the content.

## Understand the System

| Document | Covers |
| :--- | :--- |
| [architecture.md](architecture.md) | Principles, modules (current vs. target), execution pipeline, AI integration, planned protocol |
| [roadmap.md](roadmap.md) | Delivery status by phase and next priorities |

## Build Flows

| Document | Covers |
| :--- | :--- |
| [flow_markdown_spec.md](flow_markdown_spec.md) | `flow.md` syntax and compilation to `flow.json` |
| [actions_reference.md](actions_reference.md) | Every built-in action with parameters and examples |
| [project_bundles.md](project_bundles.md) | Bundle layout, `config.json`, `.env`, subflows (`flow.call`), deployment lifecycle |

## Run and Operate

| Document | Covers |
| :--- | :--- |
| [cli_guide.md](cli_guide.md) | `kinenix` commands and options |
| [hub.md](hub.md) | Running the Hub, environment variables, worker authentication |
| [logging.md](logging.md) | Execution log layout and JSON format |
| [ask_router.md](ask_router.md) | Natural-language questions to the Hub (work in progress) |
| [../kinenix-worker/README.md](../kinenix-worker/README.md) | Worker CLI and Raspberry Pi setup |
| [../kinenix-studio/README.md](../kinenix-studio/README.md) | Studio design and layout |

## Contribute

| Document | Covers |
| :--- | :--- |
| [../AGENTS.md](../AGENTS.md) | Entry point for AI assistants: commands, rules index, current vs. target state |
| [../.agents/rules/](../.agents/rules/) | Engineering rules: coding, testing, security, errors, logging, git |

Machine-readable schemas: [../schemas/flow.schema.json](../schemas/flow.schema.json), [../schemas/execution_log.schema.json](../schemas/execution_log.schema.json).

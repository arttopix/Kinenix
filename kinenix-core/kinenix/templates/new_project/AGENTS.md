# Instructions for AI assistants: {{title}}

This folder is a Kinenix flow project. Kinenix runs automation flows written in Markdown (`flow.md`). Your job is to turn the requirements in `requirements.md` into a working `flow.md`.

## Workflow

1. Read `requirements.md`. If something needed to build the flow is missing or ambiguous, ask the user before writing it.
2. Write `flow.md` following the Flow Markdown specification. Do not edit `flow.json`: it is built from `flow.md` automatically.
3. Put every value the requirements say must be changeable (URLs, lists, dates, paths, recipients) in `config/config.json` and read it as `${config.name}`.
4. Put secrets (passwords, API keys, tokens) only in `.env` (see `.env.example`) and read them as `${env.NAME}`. Never write a secret in `flow.md` or `config/config.json`.
5. Run `kinenix validate .` and fix every reported problem.
6. Run `kinenix run .`, read the log, and fix failures. Report what you verified.

## References

| Need | Where |
| :--- | :--- |
| Every action and the exact parameters it accepts | Run `kinenix actions` (or `kinenix actions web` for one group) |
| `flow.md` syntax: steps, parameters, loops, conditions, error handling | https://github.com/arttopix/Kinenix/blob/main/docs/flow_markdown_spec.md |
| Action details and examples | https://github.com/arttopix/Kinenix/blob/main/docs/actions_reference.md |
| Project layout, config, `.env`, subflows | https://github.com/arttopix/Kinenix/blob/main/docs/project_bundles.md |
| Complete working examples | `kinenix init --list`, then for example `kinenix init --example bot_fx_rate` in another folder |

## Rules

- **Web pages:** open the real page before choosing selectors; do not guess them. Prefer selectors based on visible text, labels, roles, or stable attributes over long CSS or XPath paths. If a page shows customer or other business data, ask the user to pick the selectors instead of sending the page content to a cloud service.
- **Errors:** add `on_error: retry` with `max_retries` to steps that touch the network or files. Stop on business problems (no data, invalid input) with a `flow.fail` step and a clear message.
- **Results:** write outputs under `output/`, which is not committed.
- **Keep data local:** do not send flow data to third-party services unless the requirements ask for it.
- Keep `flow.md` readable: one action per step, descriptive step names.

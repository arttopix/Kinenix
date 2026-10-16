# Instructions for AI assistants: {{title}}

This folder is a Kinenix flow project. Kinenix runs automation flows written in Markdown (`flow.md`). Your job is to turn the requirements in `requirements.md` into a working `flow.md`.

## Workflow

1. Read `requirements.md`. If something needed to build the flow is missing or ambiguous, ask the user before writing it.
2. Write `flow.md` following the Flow Markdown specification. `flow.md` is the only flow file; do not create a `flow.json`.
3. Put every value the requirements say must be changeable (URLs, lists, dates, paths, recipients) in `config/config.json` and read it as `${config.name}`.
4. Put secrets (passwords, API keys, tokens) only in `.env` (see `.env.example`) and read them as `${env.NAME}`. Never write a secret in `flow.md` or `config/config.json`.
5. List in `"redact"` in `config/config.json` every field that holds personal or confidential data (names, ID numbers, policy or account numbers, addresses), so it is hidden in logs and on the Hub. Add `- **secret:** true` to a `web.type` that types a secret into a field that is not a password field.
6. Run `kinenix validate .` and fix every reported problem.
7. Run `kinenix run .`, read the log, and fix failures. Report what you verified.

When the requirements say what to do if the bot fails (send an e-mail, take a screenshot) or what must always happen at the end (close the browser, zip the output), put those steps in `## On Error` and `## Finally` after `## Steps`, use `${error.message}`, `${error.step_name}`, and `${error.loop.item}` in them, and add the `> Requires: kinenix>=...` line under the title that `kinenix validate` asks for. Give every `logic.loop` an `item_label` that identifies the item, such as an order number.

## References

| Need | Where |
| :--- | :--- |
| Every action and the exact parameters it accepts | Run `kinenix actions` (or `kinenix actions web` for one group) |
| `flow.md` syntax: steps, parameters, loops, conditions, error handling | https://github.com/arttopix/kinenix/blob/main/docs/flow_markdown_spec.md |
| Action details and examples | https://github.com/arttopix/kinenix/blob/main/docs/actions_reference.md |
| Project layout, config, `.env`, subflows | https://github.com/arttopix/kinenix/blob/main/docs/project_bundles.md |
| Sending runs to a Hub, and why a run does not appear there | https://github.com/arttopix/kinenix/blob/main/docs/hub.md#8-how-machines-connect-and-troubleshooting |
| Complete working examples | `kinenix init --list`, then for example `kinenix init --example bot_fx_rate` in another folder |

## Rules

- **Web pages:** open the real page before choosing selectors; do not guess them. Prefer selectors based on visible text, labels, roles, or stable attributes over long CSS or XPath paths. If a page shows customer or other business data, ask the user to pick the selectors instead of sending the page content to a cloud service.
- **Errors:** add `max_retries` (and `retry_interval` in seconds) to steps that touch the network or files; add `on_error: continue` only when the flow should go on after the last attempt, for example to the next item of a loop. Stop on business problems (no data, invalid input) with a `flow.fail` step and a clear message.
- **Text with several lines** (an email body, a message): write `- **body:** |` and indent the lines below it. Lines that are not indented are ignored, and `kinenix validate` reports them.
- **Conditions:** write them as a sentence, for example `${row.note} is empty`, `${brand} in ${config.brands}`, `${label} contains 5,000`, and join them with `and`, `or`, `not`. The operators are listed in the specification under Conditions.
- **Values:** count, join, clean, pick, and calculate inside `${...}` with the expression functions in the specification (`len`, `join`, `number`, `trim`, `replace`, `default`, `round`, `part`, `substring`, ...) and `+ - * /`, for example `${len(rows)}` or `${number(row.price) * 12}`, instead of extra steps. Comparisons stay in conditions.
- **Results:** write outputs under `output/`, which is not committed.
- **Keep data local:** do not send flow data to third-party services unless the requirements ask for it.
- Keep `flow.md` readable: one action per step, descriptive step names.

## Mistakes to avoid

These are the mistakes AI assistants make most often in `flow.md`; `kinenix validate` reports each of them.

- **The action goes in the step heading**, in backticks and parentheses: `### 3. Open Page (`web.open`)`. A heading without it is not a step.
- **Sub-steps** of `logic.loop` and `logic.if` are bullets under `- **Sub-steps:**`, each with its action, and their parameters are indented below:
  ```markdown
  - **Sub-steps:**
    - Tick Currency (`web.check`):
      - **selector:** `input[value='${currency}']`
  ```
- **Only the parameters an action accepts** (`kinenix actions <prefix>` lists them); `on_error`, `max_retries`, `retry_interval`, `output_var`, and `condition` belong to every step.

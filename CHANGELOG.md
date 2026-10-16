# Changelog

`kinenix`, `kinenix-hub`, and `kinenix-worker` are released together with one version. How to release: [docs/releasing.md](docs/releasing.md).

## 0.3.0b1 (2026-10-16)

Expressions: count, join, clean, pick, and calculate values inside `${...}`, safely. Design: [docs/design/expressions.md](docs/design/expressions.md).

**Add `> Requires: kinenix>=0.3.0b1` to a flow that uses expressions or `and` / `or` / `not`** (`kinenix validate` says when). Kinenix 0.2.0b4 and older turn `${len(rows)}` into empty text and read `and` as part of a value, without an error. Upgrade every worker first.

### Flows

- Functions in `${...}`: `len`, `join`, `number`, `trim`, `lower`, `upper`, `replace`, `default`, `round`, `part`, `substring`; `+ - * / %` on numbers; indexing such as `${rows[0].id}` and `${row['Unit Price (THB)']}` (#56).
- Conditions join comparisons with `and`, `or`, and `not`; a value such as `Johnson and Johnson` is not split.
- Nothing written in a flow can run code: expressions are parsed and checked against a fixed list, without `eval`. `${x.__class__}`, which read Python internals before, now gives empty.
- A variable that exists is read as before, so keys such as `First Name` or `Role in Company` keep working. A missing key written with clear expression syntax (a function call, brackets, quotes, or `+ * / % < > = !`) now reports an error instead of giving empty.
- `kinenix validate` reports expression errors and unknown functions with their line.

### Also

- When a run cannot reach the Hub, the log says why in plain words (name not found, Hub not running, firewall), as `kinenix connect` does.
- The copyright owner is named in every LICENSE and NOTICE file.
- www.kinenix.com is rebuilt when the documentation on `main` changes.

## 0.2.0b4 (2026-10-16)

Phase 2: subflows, error handling, and run records that people and AI can query.

**Upgrade every worker before you deploy a flow that uses `## On Error` or `## Finally`.** Kinenix 0.2.0b3 and older read the steps under those headings as ordinary steps, so an older worker would, for example, send the error e-mail on every successful run. Add `> Requires: kinenix>=0.2.0b4` under a flow's title; 0.2.0b4 and newer refuse a flow that needs a newer version. Upgrading: [docs/releasing.md, section 3](docs/releasing.md#3-upgrading-an-installation).

### Flows

- `## On Error` and `## Finally` sections, `${error}` (message, step, path, subflow, line, loop item, retries, root cause, screenshot), and `${run}` (id, flow, started, status, log path) (#50, #51).
- `max_retries` always retries first; `on_error: continue` then records the failure and goes on; `max_retries`, `retry_interval`, and `config.error_dir` accept `${...}` (#52).
- `logic.loop` takes `item_label`, which names each item in logs and on the Hub and counts work items.
- Subflows are written as `.md`, share the bundle's config and folder (`@shared/` subflows keep their own unless `inherit_config: true`), and `kinenix validate` follows them (#49, #60).
- `> Requires: kinenix>=VERSION` under a flow's title.

### Run records

- One record per run: every step, including subflow steps, with its line, path, subflow, loop item, retries, and for failures how they were handled (`stopped`, `continued`, `fallback`). Subflows no longer write their own logs or send their own runs (#62).
- A live log (`.jsonl`) written while the flow runs, available as `${run.log_path}`; one screenshot per failure (#54).
- Secrets and personal data are redacted on the worker before logs, `${error}`, and the Hub.

### Hub

- Tables `step_results` and `failures`, `executions.details` with a Markdown run report, views `v_runs`, `v_failures`, and `v_steps`, and a data dictionary ([docs/hub_data.md](docs/hub_data.md)). An existing `hub.db` is upgraded in place, and its runs get their records at the first start.
- `kinenix hub query` (read-only questions, on the Hub machine or with `--url`), user views from `~/.kinenix/hub_views/`, `kinenix hub report --flow NAME`, and `kinenix hub logs --flow NAME`.
- `kinenix connect URL` saves the Hub a machine reports to, after checking the key; `kinenix hub setup` offers it for runs on the Hub machine.
- Failure summaries name a Business error as a business rule that was not met, and report an unrecognized error as unknown instead of guessing.

### Also

- License changed to Apache-2.0.
- The repository is now `arttopix/kinenix`.

# Phase 2 Design: Subflows, Error Handling, and Run Records

Status: **proposal for review** (2026-10-12). Milestone: [Phase 2: Subflows and error handling](https://github.com/arttopix/Kinenix/milestone/2). Issues: #49, #50, #51, #52, #54, #60, #62.

## 1. Goal

A person should be able to ask an AI the morning after a run, "what failed last night, and where?", and get a correct answer. The AI answers from recorded facts, not guesses. Later the Hub exposes these facts as an MCP server, so any MCP client (Claude Code, Cursor, VS Code, or a local model) can query them.

Phase 2 builds the foundation:

1. Flows handle failures in one place (`## On Error`, `## Finally`) instead of `fallback_step_id` on every step.
2. Every failure is recorded as complete, structured facts, with secrets removed on the worker.
3. The Hub stores those facts in tables and views designed to be queried by people and AI, documented in a data dictionary.
4. Subflows work like the rest of the bundle: same config, same folder, written in `flow.md` format.

Out of scope (later phases): the MCP server itself, AI analysis on the Hub, page evidence (accessibility tree, similar elements), full-text and vector search, and `logic.try` blocks.

## 2. Decisions

| # | Topic | Decision |
| :--- | :--- | :--- |
| A1 | Flow-level error handling | `## On Error` and `## Finally` sections in `flow.md` |
| A1 | Failure records | Complete structured facts (section 6), for morning questions |
| A1 | Secrets | Redacted on the worker before logs, `${error}`, or the Hub; pattern redaction is best effort |
| A2 | Retries | `max_retries` always retries first; `on_error` decides what happens after the last attempt |
| A3 | Subflow files | `flow.call` accepts `subflows/x.md`, compiled in memory on every run; no generated `x.json` |
| A4 | Subflow context | Local subflows (`./subflows/`) get the bundle's `config` and folder; data only through `inputs`. `@shared/` subflows keep their own folder and config, take values through `inputs`, or receive the caller's config with `inherit_config: true` |
| 6 | Database | SQLite; hybrid storage (stable, filtered fields as columns, the rest in a JSON `details` column) |
| 7 | Schema changes | A small built-in migration runner (no Alembic); SQLite WAL mode on |
| 8 | Tables and views | `executions` (+ `details`), `step_results`, `failures`; views `v_runs`, `v_failures`, `v_steps`; user views in `~/.kinenix/hub_views/`; a data dictionary checked by tests |
| - | Loop items | `logic.loop` gets `item_label` |
| - | Querying | `kinenix hub query` (read-only) |

## 3. `flow.md` changes

### 3.1 `## On Error` and `## Finally`

```markdown
# TIPH Quotes

## Steps
### 1. Email Start (`email.send`)
...
### 12. Email Complete (`email.send`)
...

## On Error
### 1. Capture Screen (`web.screenshot`)
- **path:** ./output/error.png
### 2. Email Error (`email.send`)
- **subject:** TIPH failed at ${error.step_name}
- **body:** |
    ${error.message}

    Item: ${error.loop.item}
    Cause: ${error.root_cause}
- **attachments:** ["./output/error.png"]

## Finally
### 1. Zip Output (`file.zip`)
- **source:** ./output
- **destination:** ./outbox/run.zip
### 2. Close Browser (`web.close`)
```

Run order:

```
1. Run Steps.
2. A step fails (after its retries, and its on_error is not continue or fallback):
     the remaining Steps are skipped; ${error} is set; On Error runs.
3. Finally runs, whether Steps succeeded or failed.
4. Result: failed if Steps failed, otherwise success. On Error does not turn a failure into a success.
```

- A `flow.fail` (business error) also runs On Error; `${error.type}` is `Business`.
- A failing step inside On Error or Finally is recorded, and the rest of that section still runs. On Error never triggers itself again.
- A subflow can have its own On Error and Finally. They run inside the subflow, then the failure continues to the caller.
- Steps in these sections are ordinary steps: parameters, `condition`, loops, and subflows work the same.

### 3.2 `${error}`

Set when a step fails (including failures handled by `on_error: continue`), so On Error and later steps can use it:

| Field | Example |
| :--- | :--- |
| `${error.message}` | `Timeout 30000ms exceeded waiting for role=option[name='HONDA']` |
| `${error.type}` | `Technical` or `Business` |
| `${error.step_id}`, `${error.step_name}`, `${error.action}` | `sub_step_3_4`, `Choose Brand`, `web.click` |
| `${error.path}` | `TIPH Quotes > Each Request > process_one > Choose Brand` (through subflows) |
| `${error.subflow}` | `process_one`, or empty |
| `${error.line}` | Line of the step in its `flow.md` |
| `${error.loop.item}`, `${error.loop.index}`, `${error.loop.of}` | `R007 HONDA HR-V`, `7`, `12` |
| `${error.retries}` | `2` |
| `${error.root_cause}`, `${error.suggested_fix}` | From the existing rule-based diagnosis |
| `${error.screenshot}` | Path of the automatic failure screenshot |

The values are redacted (section 7) before they are stored in `${error}`.

### 3.3 Retries and what happens next (#52)

```markdown
- **max_retries:** 2
- **retry_interval:** 5
- **on_error:** continue      # after 2 more attempts, record the failure and go on
```

| `on_error` | After the last attempt |
| :--- | :--- |
| (not set) or `fail` | The flow fails; On Error runs |
| `retry` | Same as `fail` (kept for existing flows) |
| `continue` | The failure is recorded (`handled = continued`) and the flow goes on |

`fallback_step_id` keeps working; the failure is recorded with `handled = fallback`. `max_retries`, `retry_interval`, and `config.error_dir` accept `${...}` (#52, #54).

### 3.4 `item_label` on `logic.loop`

```markdown
### 2. Each Request (`logic.loop`)
- **items:** `${requests}`
- **item_var:** `req`
- **item_label:** ${req.request_id} ${req.brand} ${req.model}
```

Every step result and failure inside the loop records `loop.index`, `loop.of`, and `loop.item`. Without `item_label`, `loop.item` is built from the first three scalar fields of the item, redacted.

### 3.5 Subflows (#49, #60)

```markdown
### 3. Process One Request (`flow.call`)
- **flow:** ./subflows/process_one.md
- **inputs:** {"req": "${req}"}

### 1. Log In (`flow.call`)
- **flow:** @shared/erp_login.md
- **inputs:** {"login_url": "${config.erp_url}"}

### 2. Use Shared Report (`flow.call`)
- **flow:** @shared/monthly_report.md
- **inherit_config:** true
```

| Subflow | Folder for relative paths | `${config}` | Other caller variables |
| :--- | :--- | :--- | :--- |
| `./subflows/x.md` (bundle) | The bundle root | The caller's config | Only through `inputs` |
| `@shared/x.md` | Its own folder | Its own config; the caller's with `inherit_config: true` | Only through `inputs` |

- `.md` subflows are compiled in memory on every run. No `x.json` is written. Existing `.json` subflows still work.
- `kinenix validate` follows `flow.call` targets in the bundle: it checks the subflow, and reports `inputs` keys that the subflow does not declare in its `## Variables`, with a suggestion.
- A failure inside a subflow takes one screenshot, in the subflow (#54).
- Subflows no longer write their own log files; the caller's log contains their steps (#62).

### 3.6 Guarding against older Kinenix versions

Kinenix 0.2.0b3 and older do not know `## On Error` and `## Finally`. Their parser treats the steps under these headings as ordinary steps, so an old worker would, for example, send the error email on every successful run.

- From 0.2.0b4, a flow may declare the version it needs: `> Requires: kinenix>=0.2.0b4`. Versions from 0.2.0b4 refuse to run a flow that needs a newer version, with a clear message. `kinenix validate` reports a flow that uses On Error, Finally, `item_label`, or `inherit_config` without this line.
- 0.2.0b3 and older cannot be changed. The release notes and `docs/releasing.md` say: **upgrade every worker before deploying a flow that uses On Error or Finally.** The Hub dashboard shows each worker's Kinenix version (from heartbeats) to make this visible.

## 4. Compiled form changes

Flows exist only as `flow.md` (decided after this design was first written); the structure below is the compiled form that `kinenix compile` prints and that the runner builds in memory.

```json
{
  "name": "TIPH Quotes",
  "requires": "kinenix>=0.2.0b4",
  "steps": [ ... ],
  "on_error_steps": [
    { "id": "on_error_1", "name": "Capture Screen", "action": "web.screenshot", "parameters": { "path": "./output/error.png" } }
  ],
  "finally_steps": [
    { "id": "finally_1", "name": "Close Browser", "action": "web.close", "parameters": {} }
  ]
}
```

- `on_error_steps` and `finally_steps` are optional and default to empty; their steps have the same shape as `steps`.
- Step ids in these sections are `on_error_N` and `finally_N` (sub-steps `sub_on_error_N_M`, ...), so logs show where a step came from.
- `logic.loop` parameters gain `item_label`; `flow.call` parameters gain `inherit_config`.
- `schemas/flow.schema.json`, `export-md`, and `kinenix validate` cover the new fields.

## 5. Interpreter behavior

- Each step result records: section (`steps`, `on_error`, `finally`), path through subflows, loop index, `of`, and item, retries made, the `flow.md` line, and a short redacted output summary.
- A failure creates a failure record (section 6) whether it stops the flow, is continued, or goes to a fallback.
- The execution log is written while the flow runs (one JSON line per step) to `logs/<flow>/<date>/<time>_<run_id>.jsonl`, and the final JSON log is written at the end as today. `${run.id}` and `${run.log_path}` are available to steps, so On Error or Finally can attach the log so far (#62).
- `${run.id}` can be used in paths, for example `./output/${run.id}/`, and in `config.error_dir` (#54).

## 6. What is recorded for every failure

| Fact | Source |
| :--- | :--- |
| Flow, run id, worker, Kinenix version, time | Run context |
| Step id, name, action, `flow.md` line, section | Step |
| Path through subflows, subflow name | Call stack |
| Loop item (label, index, of) | Enclosing loops |
| Retries made, how it was handled (`stopped`, `continued`, `fallback`) | Error handler |
| Error type, exception class, message | Exception |
| Root cause and suggested fix | Existing rule-based diagnosis |
| Screenshot path | Automatic capture |
| Results of the On Error steps (for example, whether the email was sent) | On Error section |
| Steps completed before the failure, items done and failed | Run summary |

## 7. Redaction on the worker

Built in PR 3; the user-facing description is in [logging.md](../logging.md#redaction). Applied to `${error}`, step output summaries, log files, and everything sent to the Hub. Best effort: pattern matching can miss values or hide too much, so the rule is also to record only what is needed.

| What | How it is found | Replaced by |
| :--- | :--- | :--- |
| Values of variables from `.env` and `${env.*}` used by the flow | Exact value match | `****` |
| Values of keys that look secret (`password`, `passwd`, `secret`, `token`, `api_key`, `apikey`, `authorization`; `cookie` and `credential` only as the whole key name) | Key name, in parameters, config, and outputs | `****` |
| Text typed into password fields (`web.type` on `type=password`) | Field type | `****` |
| Thai national ID (13 digits with a valid check digit) | Pattern | `[thai-id]` |
| Card numbers (13-19 digits with a valid Luhn check) | Pattern | `[card]` |
| Phone numbers and e-mail addresses | Pattern; on by default, `"redact_contacts": false` in config turns it off | `[phone]`, `[email]` |
| Fields the user lists in `config.redact` | Key name | `****` |

## 8. Hub database

### 8.1 Migrations and WAL

- A `schema_version` table and an ordered list of SQL steps in the Hub package. At start, the Hub applies the steps it has not applied yet, inside a transaction, and records each one. No new dependency.
- Existing `hub.db` files are upgraded in place; no data is lost. The first migration adds what Phase 2 needs to an existing database.
- SQLite runs in WAL mode (`PRAGMA journal_mode=WAL`), so workers can write while people, dashboards, and AI read.

### 8.2 Tables

Hybrid storage: stable fields that are filtered often are columns; everything else is in a JSON `details` column with a version key `"v"`. New facts are added to `details` without a migration. A test keeps the allowed `details` keys, the code, and the data dictionary in line.

**`executions`** (exists; one row per run): existing columns, plus `details`:

```json
{"v": 1, "run_id": "a1b2c3", "kinenix_version": "0.2.0b4", "items_total": 12, "items_failed": 2, "report_md": "..."}
```

**`step_results`** (new; one row per executed step, including every loop iteration, subflow steps, and On Error and Finally steps):

| Column | Type | Meaning |
| :--- | :--- | :--- |
| `id` | integer | Row id |
| `execution_id` | text | Run |
| `seq` | integer | Order within the run |
| `section` | text | `steps`, `on_error`, `finally` |
| `step_id`, `step_name`, `action` | text | Step |
| `status` | text | `success`, `failed`, `skipped` |
| `started_at`, `duration_seconds` | datetime, real | Timing |
| `details` | JSON | `v`, `line`, `path`, `subflow`, `loop {index, of, item}`, `retries`, `skipped_reason`, `output` (short, redacted) |

**`failures`** (new; one row per failure, including failures handled by `on_error: continue`, so a run that succeeded overall can still report failed items):

| Column | Type | Meaning |
| :--- | :--- | :--- |
| `id` | integer | Row id |
| `execution_id`, `step_result_id` | text, integer | Run and step |
| `failed_at` | datetime | Time |
| `flow_name`, `worker_id` | text | Copied from the run for easy filtering |
| `step_name`, `action` | text | Step |
| `error_type` | text | `Business`, `Technical` |
| `handled` | text | `stopped`, `continued`, `fallback` |
| `message` | text | Error message (a column, for future full-text search) |
| `details` | JSON | `v`, `exception`, `root_cause`, `suggested_fix`, `path`, `line`, `loop`, `retries`, `screenshot`, `on_error` results |

Indexes: `failures(failed_at)`, `failures(flow_name, failed_at)`, `step_results(execution_id, seq)`.

### 8.3 Views

Views expose JSON fields as columns, so people and AI query one flat view.

| View | Answers |
| :--- | :--- |
| `v_runs` | How many runs, success rate, duration per flow and worker |
| `v_failures` | What failed, where, which item, how it was handled (`loop_item`, `retries`, `step_path` from `details`) |
| `v_steps` | Slowest steps, steps that fail most |

**User views:** `.sql` files in `~/.kinenix/hub_views/` (setting `KINENIX_HUB_VIEWS_DIR`) are applied at Hub start. User view names start with `custom_`; Kinenix views start with `v_`, so upgrades never overwrite user views. A `.md` file with the same name documents a user view. A failing user view is reported with its file name and does not stop the Hub. Views are read-only by nature.

### 8.4 Data dictionary

`docs/hub_data.md` documents every view and table: columns, meaning, example values, and the questions each view answers. It is written for people and AI (an MCP tool will return it later). A test fails when a column or `details` key exists without documentation, or the other way round.

### 8.5 Run report

Each run gets a short Markdown report in `executions.details.report_md`, for people, email, and AI:

```markdown
# TIPH Quotes, 2026-10-12 02:00 (failed)
- Worker: rpi4, Kinenix 0.2.0b4, duration 14 min
- Items: 6 of 12 done, 1 failed, 5 not reached
- Failed: R007 HONDA HR-V at "Choose Brand" (subflow process_one, line 42), option not found after 2 retries
- On Error: screenshot saved, error email sent
```

## 9. `kinenix hub query`

Read-only queries from the terminal, on the Hub machine (reads `hub.db`) or against a remote Hub (`--url`, with the dashboard credentials). The same code will back the MCP tools.

```bash
kinenix hub query --list                          # views and tables, row counts, what they answer
kinenix hub query --describe v_failures           # columns and meaning, from the data dictionary
kinenix hub query v_failures --since yesterday    # filters: --since --flow --worker --status --filter k=v --limit
kinenix hub query "SELECT step_name, COUNT(*) FROM v_failures GROUP BY step_name"
kinenix hub query v_failures --format json        # table (default), json, csv (--output), md; --expand shows details
```

- The database is opened read-only; one statement per call; a time limit and a default row limit of 50.

## 10. Compatibility

- Flows without the new sections and fields run as before.
- `on_error: retry` keeps its meaning.
- Workers on 0.2.0b3 or older must be upgraded before they run flows that use the new sections (section 3.6).
- An existing `hub.db` is migrated in place at the first start of the new Hub.

## 11. Pull requests

| PR | Content | Issues |
| :--- | :--- | :--- |
| 1 | Hub migration runner, WAL, `schema_version` | (foundation) |
| 2 | Subflow context (`config`, folder, `inherit_config`), `.md` subflows, validate follows subflows, `hello` gets a subflow example | #49, #60 |
| 3 | Redaction on the worker | (guardrail 1) |
| 4 | `## On Error`, `## Finally`, `${error}`, `${run.*}`, `item_label`, retries then `on_error`, `> Requires:` | #50, #51, #52 |
| 5 | Run records: `step_results`, `failures`, `executions.details`, views, data dictionary and its test, run report, one screenshot per failure, live log | #54, #62 |
| 6 | `kinenix hub query`, user views folder | - |
| 7 | Docs (spec, actions reference, hub guide, quickstart), release 0.2.0b4 (Apache-2.0, upgrade note) | - |

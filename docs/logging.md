# Structured Logging & Telemetry Standards

This document describes Kinenix's structured logging architecture, directory partitioning, exception classification, and telemetry data schema. Logging rules for contributors are in `.agents/rules/logging.md`; uploading logs to the Hub is covered in [hub.md](hub.md).

---

## 1. Directory Structure & Partitioning

Kinenix records every workflow execution into **Structured JSON Logs** organized by flow name and execution date:

```text
logs/
├── rpa_challenge_solver/               # Partitioned by Flow Name
│   └── 2026-09-11/                     # Partitioned by Execution Date (YYYY-MM-DD)
│       ├── 213906_failed.json          # Format: [HHMMSS]_[status].json
│       └── 213938_success.json
└── invoice_tax_filing/
    └── 2026-09-12/
        ├── 083000_success.json
        └── 091500_failed.json
```

### Key Benefits:
- **Instant Triage:** Log filenames immediately show the execution time and status (`_success` or `_failed`), allowing developers and operations teams to spot failures without opening files.
- **Smart Directory Resolution:** Regardless of the Current Working Directory (CWD) from which a command is executed, `resolve_log_dir` automatically locates the project root and writes logs centrally to `<project_root>/logs/`.

---

## 2. JSON Log Schema Highlights

Each execution log contains comprehensive runtime and business data:

```json
{
  "$schema": "../../../schemas/execution_log.schema.json",
  "flow_name": "RPA Challenge Solver",
  "start_time": "2026-09-11 21:39:34.000000+07:00",
  "is_completed": false,
  "has_error": true,
  "failure_details": {
    "failed_step_id": "step_2",
    "failed_step_name": "Read Challenge Excel File",
    "action": "excel.read",
    "error_type": "Technical",
    "exception_class": "FileNotFoundError",
    "error_message": "Excel file not found: ./assets/challenge.xlsx",
    "root_cause": "Required file was not found during execution of step 'Read Challenge Excel File'.",
    "suggested_fix": "Verify the target file path exists and that relative paths are correctly anchored to the flow project directory.",
    "section": "steps"
  },
  "metrics": {
    "total_steps": 2,
    "successful_steps": 1,
    "failed_steps": 1,
    "skipped_steps": 0,
    "total_duration_seconds": 1.25,
    "hours_saved": 0.0
  },
  "variables": {
    "target_url": "https://rpachallenge.com/"
  },
  "step_results": [
    {
      "step_id": "step_1",
      "step_name": "Open RPA Challenge Webpage",
      "action": "web.open",
      "status": "success",
      "duration_seconds": 0.45
    },
    {
      "step_id": "step_2",
      "step_name": "Read Challenge Excel File",
      "action": "excel.read",
      "status": "failed",
      "section": "steps",
      "duration_seconds": 0.05,
      "error_message": "Excel file not found: ./assets/challenge.xlsx",
      "error_type": "Technical"
    }
  ]
}
```

`section` says where a step or the run's failure is in `flow.md`: `steps`, `on_error`, or `finally`. A run whose Steps succeeded but whose `## Finally` failed has `has_error: true` and `failure_details.section: "finally"`, and the console prints `Result: FAILED at step [finally_1] '...' in Finally`.

Timestamps are the worker's local time with its UTC offset (`+07:00` above). The offset lets the Hub convert every execution to UTC, so workers in different time zones line up on the dashboard. The run's end time is not stored separately; it is `start_time` plus `metrics.total_duration_seconds`.

### Privacy & State Sanitization
Internal runtime objects (such as Playwright browser handles, page pointers, and database connections prefixed with `__`) are automatically filtered out prior to JSON serialization, ensuring clean, serializable log files without leaking sensitive memory objects.

### Redaction

The worker removes secrets and personal data before anything leaves the run: the JSON log file, the error lines on the console, and the telemetry sent to the Hub. Only these records are changed; the flow itself keeps working with the real values. Code: `kinenix-core/kinenix/engine/redaction.py`.

| What | How it is found | Replaced by |
| :--- | :--- | :--- |
| Values from the bundle's `.env`, and of every `${env.NAME}` the flow uses | Exact value (4 characters or longer), wherever it appears | `****` |
| Environment variables whose name looks secret (`SMTP_PASSWORD`, `KINENIX_HUB_API_KEY`, ...) | Exact value | `****` |
| Values of keys that look secret: names containing `password`, `passwd`, `secret`, `token`, `api_key`, `authorization`, `private_key`, or named exactly `pwd`, `cookie(s)`, `set-cookie`, `credential(s)` | Key name, at any depth; the value is also hidden where it appears in other text | `****` |
| `password=...`, `token: ...`, `Authorization: Bearer ...` inside text (URLs, error messages) | Pattern | `****` after the key |
| Text typed by `web.type` into a `type="password"` field, or with `secret: true` | The action | `****` |
| Thai national ID (13 digits with a valid check digit) | Pattern, also for numbers read from spreadsheets | `[thai-id]` |
| Card numbers (13-19 digits that pass the Luhn check) | Pattern | `[card]` |
| Thai phone numbers and e-mail addresses | Pattern; `"redact_contacts": false` in config keeps them | `[phone]`, `[email]` |
| Fields listed in `config.redact` | Key name (case-insensitive); the values are also hidden in other text | `****` |

Known Kinenix settings that are not secret (`KINENIX_HUB_URL`, `KINENIX_WORKER_ID`, `KINENIX_FLOWS_DIR`, and the other Hub address settings) stay readable when they come from `.env`.

Fields with personal or business data are listed in the project's `config/config.json`:

```json
{
  "redact": ["customer_name", "policy_no"],
  "redact_contacts": true
}
```

Redaction is best effort. A pattern can miss a value (a secret that does not come from `.env` and sits under a harmless key name) or hide one that is not secret (about 1 in 10 random 13-digit numbers pass the Thai ID check). Record only what is needed, and keep secrets in `.env`. Workers older than 0.2.0b4 do not redact, so upgrade every worker before relying on it.

---

## 3. Exception Classification

Every failure in `failure_details.error_type` is classified as either:

| Type | Typical cause | Owner |
| :--- | :--- | :--- |
| **Technical** | Timeouts, service outages, selectors not found after retries, missing binaries | RPA developer / DevOps |
| **Business** | Invalid or inconsistent business data (e.g. invoice total does not match PO) | Business operations |

Handling requirements for each type are defined in `.agents/rules/error_handling.md`.

---

## 4. Local AI & LLM Readiness

The structured JSON log serves as clean telemetry input for on-device Small Language Models (SLMs) running locally on CPU (e.g. Qwen 2.5):

- When a step fails, the error block, selector context, and recent variable state can be provided directly to a local SLM.
- The SLM generates a plain-language root-cause explanation and suggested fix without requiring any external cloud API tokens.

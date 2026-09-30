# Structured Logging & Telemetry Standards

This document describes Kinenix's structured logging architecture, directory partitioning, exception classification, and telemetry data schema. Logging rules for contributors are in `.agents/rules/logging.md`; uploading logs to the Orchestrator is covered in [orchestrator.md](orchestrator.md).

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
  "start_time": "2026-09-11T21:39:34.000",
  "end_time": "2026-09-11T21:39:42.869",
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
    "suggested_fix": "Verify the target file path exists and that relative paths are correctly anchored to the flow project directory."
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
      "duration_seconds": 0.05,
      "error_message": "Excel file not found: ./assets/challenge.xlsx",
      "error_type": "Technical"
    }
  ]
}
```

### Privacy & State Sanitization
Internal runtime objects (such as Playwright browser handles, page pointers, and database connections prefixed with `__`) are automatically filtered out prior to JSON serialization, ensuring clean, serializable log files without leaking sensitive memory objects.

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

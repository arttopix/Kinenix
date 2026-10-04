# Logging Rules

Rules for execution logs and telemetry. The log layout and JSON format are documented in `docs/logging.md`; the schema is `schemas/execution_log.schema.json`.

---

## 1. Execution Logs

1. **Always log:** Every execution must write one structured JSON log to `logs/<flow_slug>/<YYYY-MM-DD>/<HHMMSS>_<status>.json` via `ExecutionLogger`. Do not introduce other log locations or formats.
2. **Sanitize variables:** Variables prefixed with `__` (browser handles, connections, internal objects) must never be serialized into logs or telemetry.
3. **Mask secrets:** Passwords, tokens, and authorization headers must be redacted before logging (see `security.md`).
4. **Required content:** Flow metadata, overall status, start/end timestamps, duration, per-step results, `failure_details` on error, and metrics.

---

## 2. Business Telemetry

Logs must carry business impact indicators alongside technical data:
- **Transaction counts:** items processed, succeeded, business exceptions, technical failures.
- **Time saved:** duration saved compared with manual execution.
- **Cost saved:** estimated savings based on business configuration.

---

## 3. Telemetry Upload

- Uploading to the Hub must never fail the flow: catch and log upload errors.
- Credentials for upload come only from environment variables (`KINENIX_HUB_API_KEY`), never from flow variables or `config.json`.

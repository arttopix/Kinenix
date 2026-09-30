# Security & Data Privacy Standards

This document defines credential management, data privacy constraints, and local execution boundaries for **Kinenix**.

---

## 1. Zero Credential Leakage

- **No Hardcoded Secrets:** Never hardcode passwords, API tokens, webhook URLs (e.g., LINE Channel Access Token, Teams Webhooks), or database connection strings directly in source code or `flow.json` files.
- **Environment Variables & Secret Providers:**
  - Retrieve sensitive parameters via environment variables `${env:SECRET_KEY}` or designated configuration files.
  - Configuration files containing sensitive information must be explicitly listed in `.gitignore`.
- **Log Masking:** Automatically redact sensitive parameters (passwords, tokens, authorization headers) from structured execution logs and diagnostic telemetry.

---

## 2. Local Data Privacy & Enterprise Compliance

- **On-Device Data Processing:** Corporate data, business spreadsheets (`.xlsx`), customer records, and extracted web data must be processed locally within the worker environment.
- **No Unsolicited Data Egress:** Do not send business data to third-party cloud APIs unless explicitly configured by the user in an action designed specifically for that purpose.
- **Local AI Ingestion:** When passing runtime context to SLMs for diagnosis or self-healing selectors, utilize locally hosted models to ensure zero telemetry leakage outside the host network.

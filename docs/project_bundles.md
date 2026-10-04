# Modular Project Architecture & Unattended Lifecycle

This guide documents Kinenix's **Self-Contained Project Bundle** architecture, subflow execution standards, and the complete lifecycle from development to unattended deployment.

---

## 1. Self-Contained Project Bundle Overview

Enterprise automation workflows often contain multiple sub-processes, data files, and external templates. To avoid path dependencies, broken references, or variable collisions, Kinenix organizes workflows into **Self-Contained Project Bundles**:

```text
flows/
├── @shared/                                # Cross-project reusable library
│   ├── web_login_sso.json                  # SSO login component
│   └── send_email.json                     # Reusable Gmail/SMTP component
│
└── accounting/                             # Department / Business Domain
    └── invoice_tax_filing/                 # 1 Self-Contained Project Bundle
        ├── flow.md                         # Main flow, the file you edit (source of truth)
        ├── flow.json                       # Build output of flow.md; do not edit by hand
        ├── config.json                     # Project-specific configuration (Auto-loaded)
        ├── .env                            # Optional local secrets (Git-ignored)
        ├── subflows/                       # Project-specific subflows
        │   ├── download_tax_pdf.json
        │   └── extract_table.json
        └── assets/                         # Local templates, configs, test data
            └── tax_template.xlsx
```

### Key Principles:
- **Portability:** All references to assets and subflows inside a project bundle use **Relative Paths** (e.g. `./assets/tax_template.xlsx`, `./subflows/extract_table.json`).
- **No Hardcoded Absolute Paths:** Workflows never depend on developer-specific paths (e.g., `C:\Users\Dev\...`), ensuring seamless portability across different machines, VMs, or operating systems.
- **Atomic Units:** A single project directory represents one coherent unit of business automation that can be developed, tested, versioned, and deployed as a standalone bundle.
- **Decoupled Settings (`config.json`):** Engine automatically auto-loads `config.json` from the flow bundle directory into `${config.*}` and top-level variables. Business users or admins can modify endpoints, email recipients, or thresholds without altering `flow.json`.
- **Local Secrets (`.env`):** Optional project-level `.env` is automatically parsed and mapped to `${env.*}` for local execution without leaking credentials to version control.

---

## 2. Calling Subflows (`flow.call`)

The `flow.call` action enables modular execution of child workflows:

### 2.1 Local Project Subflow (Relative Path)
To invoke a subflow located within the same project bundle:

```json
{
  "id": "step_extract",
  "name": "Extract Table Data",
  "action": "flow.call",
  "parameters": {
    "flow": "./subflows/extract_table.json",
    "inputs": {
      "pdf_path": "${downloaded_pdf}"
    }
  },
  "output_var": "extracted_data"
}
```

### 2.2 Global Shared Component (`@shared/` Namespace)
To invoke a reusable organization-wide component from the central `@shared/` directory:

```json
{
  "id": "step_notify",
  "name": "Send LINE Alert",
  "action": "flow.call",
  "parameters": {
    "flow": "@shared/notify_line.json",
    "inputs": {
      "message": "Invoice tax filing completed successfully."
    }
  }
}
```

### 2.3 Variable Scope Isolation
- When `flow.call` executes a subflow, the child flow receives its own isolated `ExecutionContext`.
- Only explicitly mapped `inputs` and system runtime sessions (e.g. active Playwright browser sessions) are shared with the child flow.
- Internal variables within the subflow do not overwrite the caller's variables, preventing side effects and state pollution.

---

## 3. Flow Lifecycle & Unattended Deployment Strategy

The project bundle structure directly enables a robust deployment pipeline to unattended robot workers (`kinenix-worker`):

> **Status:** Phase 1 and the sandbox workspace in Phase 4 (`kinenix-worker run --sandbox`) are implemented. Packaging, Orchestrator distribution, the worker cache, and WebSocket streaming (Phases 2, 3, 5) are planned. See [roadmap.md](roadmap.md).

```text
[ Developer Machine ] -> [ Kinenix Orchestrator ] -> [ Unattended Worker Daemon ]
  Local Dev & Test          Package & Version          Isolated Sandbox Execution
```

### Phase 1: Local Development & Verification
- Developer authors and tests the workflow locally within `flows/<dept>/<project>/`.
- Run and debug via CLI: `kinenix run <project_name>`.
- All assets remain inside `./assets/` and logs are written to central `logs/`.

### Phase 2: Packaging & Versioning
- The project bundle directory is packaged into a versioned archive (e.g. `invoice_tax_filing-1.0.0.kinpkg` or `.zip`).
- Any referenced `@shared/` flows are inlined by the packaging tool into the bundle, ensuring the archive is 100% self-contained.
- The package is published to **Kinenix Orchestrator**.

### Phase 3: Distribution & Local Worker Cache
- Background daemons (`kinenix-worker`) running on target worker machines (Windows VMs, PCs, or Raspberry Pi) connect to Orchestrator via WebSocket.
- When a job is dispatched, the worker checks its local package cache (`~/.kinenix/packages/` or `C:\ProgramData\Kinenix\packages\`).
- If the requested version is not present or updated, the worker downloads and verifies the package archive.

### Phase 4: Sandbox Workspace Isolation
- Prior to execution, the worker unpacks the project bundle into an isolated, per-job workspace directory:
  ```text
  ~/.kinenix/workspaces/job_20260911_001/
  ├── flow.json
  ├── subflows/
  └── assets/
  ```
- This ensures complete filesystem isolation, eliminates cross-job file locking or corruption, and allows clean workspace disposal after job completion.

### Phase 5: Execution & Telemetry
- Worker executes the bundle: `kinenix run .../flow.json`.
- Step results, business metrics, and failure screenshots are streamed in real time to the Orchestrator dashboard.

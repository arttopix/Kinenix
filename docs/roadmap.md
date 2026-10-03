# Roadmap

This is the single source for delivery status and priorities. Statuses reflect the code in the repository, not intentions. Architecture details live in [architecture.md](architecture.md).

Legend: `[x]` done, `[~]` partially done, `[ ]` not started.

---

## 1. Next Priorities

Ordered so that safety and predictable runtime behavior come before new distributed features.

| # | Item | Status |
| :--- | :--- | :--- |
| 1 | Studio path containment and CORS restriction | Done |
| 2 | Retry and fallback runtime behavior with tests | Done |
| 3 | Orchestrator worker authentication (API key) | Done |
| 4 | Continuous integration for Python tests and the Studio frontend build | Done |
| 5 | Orchestrator dashboard authentication, CORS, and safe default host | Done |
| 6 | Persistent Studio sessions, single-step execution, and live telemetry | Not started |
| 7 | Worker WebSocket protocol and job dispatch from the Orchestrator | Not started |

### 1.4 Continuous Integration

GitHub Actions workflow `.github/workflows/ci.yml` runs on pushes and pull requests to `main` and `dev`:

- [x] Python 3.10 and 3.14 on Ubuntu, and Python 3.10 on Windows.
- [x] Installs `kinenix-core`, `kinenix-worker`, `kinenix-studio`, and `kinenix-orchestrator` with development dependencies.
- [x] Runs every pytest suite, including `kinenix-orchestrator/tests`.
- [x] Builds the Studio frontend with `npm ci` and `npm run build`.
- [x] CI status badge in the README.
- [ ] Formatting, linting, type checking, dependency vulnerability checks, and JSON schema validation of the flows in `flows/`.
- [ ] Publish `kinenix` to PyPI from a tagged release (Trusted Publishing).

### 1.5 Orchestrator Hardening

- [x] Protect the dashboard page and read endpoints (HTTP Basic Auth, localhost-only when unset).
- [x] Remove the permissive CORS policy; the dashboard is served same-origin.
- [x] Default the bind host to `127.0.0.1`, requiring an explicit opt-in to listen on the network.
- [ ] Run AI failure analysis in the background so telemetry ingestion does not wait on the LLM.
- [ ] Document an HTTPS reverse proxy setup (e.g. Caddy or nginx).

### 1.6 Persistent Studio Sessions and Debugging

- Maintain one Playwright browser and context per explicit Studio session.
- Add a "run this step" API that executes against the retained browser state.
- Stream interpreter events: step state, logs, errors, variable snapshots, screenshots.
- Add breakpoints and an element picker that returns robust selector candidates.
- Define session ownership, expiration, cleanup, and isolation so sessions do not leak browser processes.

### 1.7 Worker WebSocket Protocol and Orchestrator Dispatch

```text
Orchestrator -> versioned job bundle -> Worker (WebSocket) -> kinenix-core executes flow
                                              |
                                              +-> status, logs, metrics, screenshots -> Orchestrator
```

- Authenticate workers and authorize job delivery (per-worker credentials).
- Require job acknowledgement and use idempotency keys to prevent duplicate execution after reconnects.
- Support reconnects, cancellation, timeouts, heartbeats, and clear job state transitions.
- Package and version bundles so a worker runs the intended immutable artifact.
- Upload execution artifacts safely and retain structured audit logs.
- Follow the Hybrid Protocol in [architecture.md](architecture.md#5-agent-to-agent-hybrid-protocol-planned).

---

## 2. Phases

### Phase 1: Core Engine (`kinenix-core`) - Done
- [x] Flow JSON schema and Pydantic v2 models
- [x] Interpreter, execution context, and `${var}` evaluator (no `eval`)
- [x] Actions: Web (Playwright), Excel/CSV, file system, HTTP, email, logic, flow control
- [x] Error handling: `on_error` with `continue`, `retry`, and `fallback_step_id`; failure screenshots
- [x] Hierarchical structured logging (`logs/<flow>/<date>/<HHMMSS>_<status>.json`)
- [x] CLI and smart flow resolver (`kinenix list`, `kinenix run <flow>`)
- [x] Project bundles (`flow.call`, `@shared/`, `config.json`, `.env`)
- [x] `flow.md` authoring format with compiler to `flow.json`
- [x] Local AI actions: `ai.prompt`, `ai.extract` (Ollama), `ai.decide` (OpenThai-SystemOne)

### Phase 2: Studio (`kinenix-studio`) - In progress
- [x] FastAPI backend: flow discovery, read/save with schema validation, step update, action metadata, run
- [x] Path containment to `flows/` and restricted CORS
- [x] React/Vite 3-column UI (step timeline, inspector, context panel) served by the backend
- [ ] Persistent browser session and single-step execution (`POST /api/session/step`)
- [ ] Element picker with multi-layer selectors (role/text, CSS, XPath)
- [ ] Live debugger over WebSocket: step highlighting, variable watcher, error screenshot viewer
- [ ] AI prompt bar for natural-language flow generation
- [ ] Tauri desktop shell

### Phase 3: Orchestrator (`kinenix-orchestrator`) - In progress
- [x] FastAPI service with heartbeat and telemetry ingestion over HTTP
- [x] Execution and worker storage via SQLAlchemy (SQLite default, `DATABASE_URL` for others)
- [x] Web dashboard for workers and executions
- [x] AI failure classification with rule-based fallback
- [x] Worker API key authentication
- [x] Dashboard authentication (HTTP Basic Auth)
- [x] No CORS policy and localhost-only default bind address
- [ ] Background AI analysis and HTTPS deployment guide (see 1.5)
- [ ] PostgreSQL + Redis job queue
- [ ] Business ROI dashboard: hours saved, cost saved, transaction audit trail
- [ ] Alerts and daily digests (LINE Messaging API first, then Teams and Email)
- [~] Natural-language questions about jobs and workers with a local model (see [ask_router.md](ask_router.md))

### Phase 4: Worker (`kinenix-worker`) - In progress
- [x] `kinenix-worker run`, `watch` (file trigger), `schedule` (interval), `daemon` (multi-trigger config)
- [x] Optional per-job sandbox workspace (`~/.kinenix/workspaces/<job_id>`)
- [x] Verified on Raspberry Pi 4 (ARM64) with setup script
- [x] Heartbeat sender to the Orchestrator (`kinenix-worker ping`, busy/online/offline status)
- [x] systemd service installed by the setup script (`install_service.sh`), starts the daemon at boot
- [ ] WebSocket job client (see 1.7)
- [ ] Bundle packaging (`.kinpkg`), download, and local cache
- [ ] Real-time log and screenshot streaming

### Phase 5: Desktop Automation and Public Release - Not started
- [ ] Windows desktop automation (`uiautomation` / UIA)
- [ ] Credential vault for flow secrets
- [ ] Docker Compose one-command deployment
- [ ] Community quickstart documentation

### Phase 6: Advanced Local Agentic Capabilities - Not started
- [ ] Self-healing UI selectors with DOM fallback matching
- [ ] Studio copilot for natural-language flow generation and error diagnosis
- [ ] GitOps release pipeline to Orchestrator and workers

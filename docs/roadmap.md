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
| 3 | Hub worker authentication (API key) | Done |
| 4 | Continuous integration for Python tests and the Studio frontend build | Done |
| 5 | Hub dashboard authentication, CORS, and safe default host | Done |
| 6 | Persistent Studio sessions, single-step execution, and live telemetry | Not started |
| 7 | Worker WebSocket protocol and job dispatch from the Hub | Not started |

### 1.4 Continuous Integration

GitHub Actions workflow `.github/workflows/ci.yml` runs on pushes and pull requests to `main` and `dev`:

- [x] Python 3.10 and 3.14 on Ubuntu, and Python 3.10 on Windows.
- [x] Installs `kinenix-core`, `kinenix-worker`, `kinenix-studio`, and `kinenix-hub` with development dependencies.
- [x] Runs every pytest suite, including `kinenix-hub/tests`.
- [x] Builds the Studio frontend with `npm ci` and `npm run build`.
- [x] CI status badge in the README.
- [x] Repository rules checked by tests: every `flow.json` matches its `flow.md`, every flow validates, documented action parameters match the code, and no emojis anywhere.
- [ ] Formatting, linting, type checking, dependency vulnerability checks, and JSON schema validation of the flows in `flows/`.
- [~] Publish `kinenix`, `kinenix-hub`, and `kinenix-worker` from a tagged release with Trusted Publishing (`release.yml`, `docs/releasing.md`); CI builds, checks, and installs the packages on every pull request. Waiting for the first release.

### 1.5 Hub Hardening

- [x] Protect the dashboard page and read endpoints (HTTP Basic Auth, localhost-only when unset).
- [x] Remove the permissive CORS policy; the dashboard is served same-origin.
- [x] Default the bind host to `127.0.0.1`, requiring an explicit opt-in to listen on the network.
- [x] Escape all worker-provided text in the dashboard (XSS), with a static check and a real-browser test.
- [ ] Content-Security-Policy header for the dashboard (needs the inline `onclick` handlers moved to script).
- [ ] Run AI failure analysis in the background so telemetry ingestion does not wait on the LLM.
- [ ] Document an HTTPS reverse proxy setup (e.g. Caddy or nginx).

### 1.6 Persistent Studio Sessions and Debugging

- Maintain one Playwright browser and context per explicit Studio session.
- Add a "run this step" API that executes against the retained browser state.
- Stream interpreter events: step state, logs, errors, variable snapshots, screenshots.
- Add breakpoints and an element picker that returns robust selector candidates.
- Define session ownership, expiration, cleanup, and isolation so sessions do not leak browser processes.

### 1.7 Worker WebSocket Protocol and Hub Dispatch

```text
Hub -> versioned job bundle -> Worker (WebSocket) -> kinenix-core executes flow
                                              |
                                              +-> status, logs, metrics, screenshots -> Hub
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
- [x] `flow.md` as the single source with automatic `flow.json` sync and a CI consistency check
- [x] Flow validation (`kinenix validate`): unknown actions and ignored parameters, with suggestions
- [x] Business exceptions with `flow.fail` (recorded as Business, never retried); `web.click` waits for a response; `web.get_table`
- [x] `email.send` through any SMTP provider (Gmail, Microsoft 365, company servers), tested with a local fake SMTP server
- [x] Example flow `bot_fx_rate`: Bank of Thailand transfer rates to CSV and email, verified against the BOT data
- [x] `file.zip` and `file.unzip`: pack a run's output for an email attachment; extraction refuses entries that point outside the destination
- [x] `file.list` (loop over the files in a folder, newest first), `file.read_text` and `file.write_text` (text, lines, JSON, append, Thai legacy encodings), `file.create_folder`; boolean parameters given as text in config ("false") are read correctly by all file actions

### Phase 2: Studio (`kinenix-studio`) - In progress
- [x] FastAPI backend: flow discovery, read/save with schema validation, step update, action metadata, run
- [x] Path containment to `flows/` and restricted CORS
- [x] React/Vite 3-column UI (step timeline, inspector, context panel) served by the backend
- [ ] Persistent browser session and single-step execution (`POST /api/session/step`)
- [ ] Element picker with multi-layer selectors (role/text, CSS, XPath)
- [ ] Live debugger over WebSocket: step highlighting, variable watcher, error screenshot viewer
- [ ] AI prompt bar for natural-language flow generation
- [ ] Tauri desktop shell

### Phase 3: Hub (`kinenix-hub`) - In progress
- [x] Renamed from Orchestrator to Hub; old command, flags, environment variables, and settings file still work (see [hub.md](hub.md#5-renamed-from-orchestrator))
- [x] FastAPI service with heartbeat and telemetry ingestion over HTTP
- [x] Execution and worker storage via SQLAlchemy (SQLite default, `DATABASE_URL` for others)
- [x] Web dashboard for workers and executions, with per-execution step details
- [x] Command line: first-run setup saved to `~/.kinenix/hub.env`, `kinenix hub status`, `logs`, `setup`, `show-key`, and `rich` output
- [x] Default database in `~/.kinenix/hub.db`, outside the source tree
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
- [x] Verified on Raspberry Pi 4 (ARM64) with setup script; re-verified on 2026-10-05 after the rename to Hub: heartbeats as a systemd service and the `bot_fx_rate` flow run by a cron trigger, reported to the Hub
- [x] Heartbeat sender to the Hub (`kinenix-worker ping`, busy/online/offline status), with `rich` output
- [x] systemd service installed by the setup script (`install_service.sh`), starts the daemon at boot
- [x] Cron schedules (`"cron": "0 8 1 * *"` in `triggers.json`, `kinenix-worker schedule --cron`)
- [ ] WebSocket job client (see 1.7)
- [ ] Bundle packaging (`.kinpkg`), download, and local cache
- [ ] Real-time log and screenshot streaming

### Phase 5: Desktop Automation and Public Release - Not started
- [ ] Windows desktop automation (`uiautomation` / UIA)
- [ ] Credential vault for flow secrets
- [ ] Docker Compose one-command deployment
- [x] Community quickstart documentation ([quickstart.md](quickstart.md))
- [x] `kinenix init "Task name"`: new project for the requirements-to-AI-to-`flow.md` workflow (`requirements.md`, `AGENTS.md` for the assistant, `.env.example`); `kinenix init --example` with packaged examples (`hello`, `bot_fx_rate`, `rpachallenge`); `kinenix actions` lists actions and their parameters
- [x] User flows live in a flows folder outside the Kinenix repository (default `~/kinenix-flows`, asked on the first `kinenix init`, optional git repository, `kinenix flows-dir`, `KINENIX_FLOWS_DIR`); `kinenix run NAME` and worker triggers find flows there by name

### Phase 6: Advanced Local Agentic Capabilities - Not started
- [ ] Self-healing UI selectors with DOM fallback matching
- [ ] Studio copilot for natural-language flow generation and error diagnosis
- [ ] GitOps release pipeline to Hub and workers

# Central Orchestrator Guide

The Central Orchestrator (`kinenix-orchestrator`) receives worker heartbeats and execution telemetry, stores them in a database, and serves the web dashboard with AI-assisted failure summaries.

---

## 1. Starting the Orchestrator

Install it once (it is a separate package from `kinenix-core`):

```powershell
pip install -e kinenix-orchestrator
```

```powershell
# Local only (default): dashboard at http://127.0.0.1:8080
kinenix orchestrator

# Accept remote workers and viewers: set credentials first (sections 2 and 3)
kinenix orchestrator --host 0.0.0.0 --port 8080
```

The Orchestrator listens on `127.0.0.1` by default, so nothing on the network can reach it until you opt in with `--host 0.0.0.0` (or `ORCHESTRATOR_HOST`). The startup banner shows the address it listens on, the URL to open in a browser, the URL workers should use (`Worker URL`, the machine's LAN address when bound to `0.0.0.0`), and whether the worker API key and dashboard password are set.

### Saved Settings (First Run)

The first time `kinenix orchestrator` runs in an interactive terminal, it asks a few questions and saves the answers, so later starts need no flags or environment variables:

1. Allow workers on other machines to connect (binds to `0.0.0.0` instead of `127.0.0.1`)
2. Port
3. Worker API key, with hidden input; press Enter to generate one
4. Dashboard password, typed twice; press Enter to keep the dashboard localhost-only

| Command | Purpose |
| :--- | :--- |
| `kinenix orchestrator` | Start; runs the questions on first use |
| `kinenix orchestrator setup` | Change the saved answers (Enter keeps the current key and password) |
| `kinenix orchestrator show-key` | Print the worker API key to copy to workers |
| `kinenix orchestrator --no-prompt` | Never ask (services and scripts) |

The answers are stored in `~/.kinenix/orchestrator.env` (override with `ORCHESTRATOR_SETTINGS_FILE`), outside the repository. The dashboard password is stored only as a salted PBKDF2 hash; the worker API key is stored as is, because the server must compare it, so the file is made owner-readable only on Linux and macOS. Environment variables and the `--host` / `--port` flags always take precedence over the file.

`kinenix orchestrator status` asks for the dashboard password when the server requires one and `ORCHESTRATOR_DASHBOARD_PASSWORD` is not set.

On Windows, remote workers also need an inbound firewall rule for the port, and the network must be in the profile the rule applies to (run as Administrator):

```powershell
Set-NetConnectionProfile -InterfaceAlias "<adapter>" -NetworkCategory Private   # only on a trusted home or office network
New-NetFirewallRule -DisplayName "Kinenix Orchestrator 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -RemoteAddress LocalSubnet -Action Allow -Profile Private
```

### Checking Status from the Command Line

The dashboard is optional. From a second terminal, `kinenix orchestrator status` shows workers (status, current task, CPU, RAM, last heartbeat) and recent executions with failure summaries:

```powershell
kinenix orchestrator status                                   # http://127.0.0.1:8080
kinenix orchestrator status --url http://<orchestrator-ip>:8080 --limit 20
```

It reads `ORCHESTRATOR_DASHBOARD_USER` and `ORCHESTRATOR_DASHBOARD_PASSWORD` from the environment, so set them to the server's values when a dashboard password is configured ([section 3](#3-dashboard-authentication)).

No CORS policy is configured: the dashboard is served from the Orchestrator's own origin, and workers call the API directly rather than from a browser, so other websites cannot read Orchestrator data through a visitor's browser.

### Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `ORCHESTRATOR_API_KEY` | *(unset)* | Shared secret workers must send in the `X-API-Key` header. See [Worker Authentication](#2-worker-authentication). |
| `ORCHESTRATOR_DASHBOARD_USER` | `admin` | Username for the dashboard login. See [Dashboard Authentication](#3-dashboard-authentication). |
| `ORCHESTRATOR_DASHBOARD_PASSWORD` | *(unset)* | Password for the dashboard login. |
| `DATABASE_URL` | `sqlite:///kinenix-orchestrator/kinenix_orchestrator/orchestrator.db` | SQLAlchemy connection string (e.g. PostgreSQL). |
| `CENTRAL_LLM_URL` | `http://127.0.0.1:8000/v1/systemone` | LLM endpoint used for failure analysis. |
| `ORCHESTRATOR_HOST` / `ORCHESTRATOR_PORT` | `127.0.0.1` / `8080` | Bind address and port. The CLI flags `--host` / `--port` override them. Use `0.0.0.0` to accept remote connections. |
| `ORCHESTRATOR_SETTINGS_FILE` | `~/.kinenix/orchestrator.env` | Saved settings written by `kinenix orchestrator setup`. See [Saved Settings](#saved-settings-first-run). |
| `ORCHESTRATOR_WORKER_OFFLINE_SECONDS` | `90` | A worker with no heartbeat for this long is shown as `offline`. Keep it above three times the workers' `KINENIX_HEARTBEAT_INTERVAL`. |

---

## 2. Worker Authentication

The Orchestrator has two independent credentials: an API key for workers (this section) and a username/password for people viewing the dashboard ([section 3](#3-dashboard-authentication)). Neither grants the other's access.

| Endpoint | Protected by |
| :--- | :--- |
| `POST /api/v1/heartbeat` | Worker API key |
| `POST /api/v1/telemetry` | Worker API key |
| `POST /api/v1/executions/{id}/reanalyze` | Worker API key |
| `GET /` (dashboard page) | Dashboard login |
| `GET /api/v1/workers`, `/api/v1/executions`, `/api/v1/executions/{id}` | Dashboard login |
| `GET /api/v1/healthz`, `/static/*` | Public (no data) |

### 2.1 Behavior

| `ORCHESTRATOR_API_KEY` | Request | Result |
| :--- | :--- | :--- |
| Set | Matching `X-API-Key` header | `200 OK` |
| Set | Missing or wrong key (from any host, including localhost) | `401 Unauthorized` |
| Unset | From localhost (`127.0.0.1` / `::1`) | Accepted (local development mode) |
| Unset | From another machine | `403 Forbidden` |

When the key is unset, the Orchestrator still binds to the network but refuses remote writes, so a forgotten key never leaves the server open. The active mode is logged at startup.

### 2.2 Setup

1. Generate a random key:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Start the Orchestrator with the key:

   ```powershell
   $env:ORCHESTRATOR_API_KEY = "<generated-key>"
   kinenix orchestrator
   ```

3. On every worker, set the same key and point telemetry at the Orchestrator:

   ```powershell
   $env:KINENIX_ORCHESTRATOR_API_KEY = "<generated-key>"
   kinenix run flows/examples/BOT --orchestrator http://<orchestrator-ip>:8080
   ```

   The Orchestrator URL can also be set with `KINENIX_ORCHESTRATOR_URL` instead of `--orchestrator`.

4. Verify from a worker machine:

   ```powershell
   kinenix-worker ping
   ```

   `ping` reports whether the Orchestrator is reachable and whether the key is accepted. Without kinenix-worker, send a heartbeat by hand:

   ```powershell
   curl.exe -X POST http://<orchestrator-ip>:8080/api/v1/heartbeat `
     -H "X-API-Key: <generated-key>" -H "Content-Type: application/json" `
     -d '{\"worker_id\": \"test-worker\"}'
   ```

   A `401` response means the key is missing or does not match; a `403` means the Orchestrator has no key configured.

Workers started with `kinenix-worker` send heartbeats on their own; see the [worker guide](../kinenix-worker/README.md#d-connect-to-the-orchestrator).

If the Orchestrator rejects telemetry, the worker logs a warning asking you to check `KINENIX_ORCHESTRATOR_API_KEY`. The flow itself still completes; only the telemetry upload fails.

### 2.3 Security Notes

- **Environment variables only:** The key is read from environment variables, never from `config.json` or flow variables, so it cannot be committed to git or written into execution logs.
- **Reverse proxy:** When a reverse proxy runs on the same machine, every request appears to come from localhost. Always set `ORCHESTRATOR_API_KEY` in that setup.
- **Use HTTPS across networks:** The key travels in a plain header. Put the Orchestrator behind HTTPS (e.g. a TLS-terminating reverse proxy) when workers connect over untrusted networks.
- **Single shared key:** All workers currently share one key. Rotating it requires updating every worker.

---

## 3. Dashboard Authentication

The dashboard page and its read endpoints use HTTP Basic Auth. Browsers show a built-in login prompt when the page opens and reuse the credentials for the dashboard's API calls, so no separate login page is needed.

### 3.1 Behavior

| `ORCHESTRATOR_DASHBOARD_PASSWORD` | Request | Result |
| :--- | :--- | :--- |
| Set | Correct username and password | `200 OK` |
| Set | Missing or wrong credentials (from any host, including localhost) | `401 Unauthorized` (browser shows login prompt) |
| Unset | From localhost | Accepted (local development mode) |
| Unset | From another machine | `403 Forbidden` |

### 3.2 Setup

```powershell
$env:ORCHESTRATOR_DASHBOARD_USER = "admin"            # optional, defaults to admin
$env:ORCHESTRATOR_DASHBOARD_PASSWORD = "<strong-password>"
kinenix orchestrator
```

Open `http://<orchestrator-ip>:8080` and sign in. For scripts, pass the same credentials:

```powershell
curl.exe -u admin:<strong-password> http://<orchestrator-ip>:8080/api/v1/executions
```

### 3.3 Security Notes

- **Use HTTPS across networks:** Basic Auth sends the password encoded but not encrypted on every request.
- **Signing out:** Browsers cache Basic Auth credentials until the browser is closed; there is no logout button.
- **Single account:** There is one shared dashboard account. Per-user accounts and roles are not implemented.
- **Reverse proxy:** As with the worker key, always set the password when a reverse proxy on the same machine forwards requests.

---

## 4. Timestamps

- **Storage:** All timestamps are stored in UTC. Timestamps received from workers are converted using their UTC offset.
- **Workers without an offset:** Older kinenix-core releases send local time without an offset. These timestamps are treated as the Orchestrator host's local time, which is only correct when the worker and the Orchestrator share a time zone.
- **API output:** Every timestamp is returned in ISO 8601 with an explicit `+00:00` offset. The dashboard converts it to the viewer's local time.
- **Existing databases:** Rows written before this behavior mix worker local time and UTC. For test data, delete the SQLite file and let the Orchestrator recreate it.

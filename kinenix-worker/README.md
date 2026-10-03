# kinenix-worker

The unattended robot worker daemon and edge execution engine for **kinenix**.

---

## 1. Overview

`kinenix-worker` is designed to run unattended automation workloads on edge hardware, dedicated worker machines, virtual machines, and low-power devices such as **Raspberry Pi 4 Model B**.

### Key Capabilities
- **Lightweight Execution:** Minimal overhead with direct integration into `kinenix-core`.
- **Sandbox Workspace Isolation:** Executes project bundles inside disposable, per-job sandbox environments.
- **Hardware Telemetry:** Gathers CPU, memory, architecture, and platform metrics at runtime.
- **Structured JSON Auditing:** Stores hierarchical execution traces and error telemetry locally.

---

## 2. Raspberry Pi 4 Model B (ARM64) Quickstart

### Prerequisites
- **Hardware:** Raspberry Pi 4 Model B (Rev 1.4 or compatible) with 2GB, 4GB, or 8GB RAM.
- **Operating System:** Raspberry Pi OS (64-bit Debian bookworm / bullseye) or Ubuntu Server ARM64.
- **Network:** Internet access for initial setup and downloading benchmark web pages.

### Automated Setup
Clone the repository and run the setup script:

```bash
# 1. Clone repository onto Raspberry Pi
git clone -b dev https://github.com/arttopix/Kinenix.git kinenix
cd kinenix

# 2. Grant execute permissions and run the setup script
chmod +x kinenix-worker/scripts/setup_rpi.sh
./kinenix-worker/scripts/setup_rpi.sh
```

The script automatically:
1. Installs required Linux shared libraries for Chromium on aarch64.
2. Creates a Python 3.10+ virtual environment (`.venv`).
3. Installs `kinenix-core` and `kinenix-worker` in editable mode.
4. Installs the ARM64 Playwright Chromium browser.
5. Verifies the installation with `kinenix-worker info`.
6. Installs and starts the `kinenix-worker` systemd service (see [section 3E](#e-run-as-a-systemd-service)). Pass `--no-service` to skip it.

---

## 3. Running Workflows on Raspberry Pi

### A. Activate Environment
```bash
source .venv/bin/activate
```

### B. Verify System Information
```bash
kinenix-worker info
```

Expected output on Raspberry Pi 4:
```text
Kinenix Worker System Information:
-------------------------------
  os: Linux
  os_release: 6.6.x+rpt-rpi-v8
  machine: aarch64
  processor: aarch64
  python_version: 3.11.x
  cpu_count: 4
  memory_total_mb: 3884.2
  memory_available_mb: 3200.1
  memory_used_percent: 17.6
  worker_id: raspberrypi
  orchestrator_url: (not set)
  orchestrator_api_key: (not set)
```

### C. Run RPA Challenge Example Flow
```bash
kinenix-worker run flows/examples/rpachallenge/flow.json
```

To run inside an isolated sandbox directory:
```bash
kinenix-worker run flows/examples/rpachallenge/flow.json --sandbox
```

### D. Connect to the Orchestrator

The worker reports to a Central Orchestrator when these environment variables are set (see [Orchestrator Guide](../docs/orchestrator.md) for the server side):

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `KINENIX_ORCHESTRATOR_URL` | *(unset: no reporting)* | Orchestrator base URL, for example `http://192.168.1.132:8080` |
| `KINENIX_ORCHESTRATOR_API_KEY` | *(unset)* | Must match `ORCHESTRATOR_API_KEY` on the Orchestrator |
| `KINENIX_WORKER_ID` | host name | Name shown on the dashboard and attached to every execution |
| `KINENIX_HEARTBEAT_INTERVAL` | `30` | Seconds between heartbeats while a worker command runs |

```bash
export KINENIX_ORCHESTRATOR_URL=http://192.168.1.132:8080
export KINENIX_ORCHESTRATOR_API_KEY="<key>"
export KINENIX_WORKER_ID=rpi4-01

kinenix-worker ping          # checks reachability and the API key; exit code 1 on failure
kinenix-worker run flows/examples/rpachallenge
```

With the URL set:

- Every run sends its execution log to the Orchestrator. `--log-dir` is not needed; it only controls whether a local log file is also written.
- Every run reports the worker as busy while the flow runs and online when it finishes.
- Every command that runs flows (`run`, `watch`, `schedule`, `daemon`) also sends a heartbeat every `KINENIX_HEARTBEAT_INTERVAL` seconds, including during long flows. The dashboard shows the worker as offline when heartbeats stop.
- If the Orchestrator is unreachable, flows still run. The worker logs one warning, then logs again when the connection recovers.

### E. Run as a systemd Service

The service keeps `kinenix-worker daemon` running in the background, starts it at boot, and restarts it within 10 seconds if it stops. It runs as the user who installed it, from the repository directory, so relative flow paths such as `flows/examples/rpachallenge` work. While it runs, the worker sends heartbeats and shows as online in the Orchestrator.

`setup_rpi.sh` installs it. To install or update it on an existing setup, run as your normal user (not root):

```bash
./kinenix-worker/scripts/install_service.sh
```

It reads two files in `~/.kinenix/`, creating them if they do not exist (existing files are never overwritten):

| File | Contents |
| :--- | :--- |
| `worker.env` | `KINENIX_ORCHESTRATOR_URL`, `KINENIX_ORCHESTRATOR_API_KEY`, `KINENIX_WORKER_ID` as `export` lines; owner-readable only. Add `source ~/.kinenix/worker.env` to `~/.bashrc` to use the same values in your shell. |
| `triggers.json` | Triggers for the daemon. The default `{"triggers": []}` runs no flows and only sends heartbeats. |

Example `triggers.json`:

```json
{
  "triggers": [
    { "type": "scheduler", "flow": "flows/examples/rpachallenge", "interval_seconds": 3600 },
    { "type": "file_watcher", "flow": "flows/my_excel_bot", "watch_dir": "/home/pi/inbox", "pattern": "*.xlsx" }
  ]
}
```

| Task | Command |
| :--- | :--- |
| Apply changes to `worker.env` or `triggers.json` | `sudo systemctl restart kinenix-worker` |
| Status | `systemctl status kinenix-worker` |
| Follow logs | `journalctl -u kinenix-worker -f` |
| Stop until next boot | `sudo systemctl stop kinenix-worker` |
| Remove the service | `./kinenix-worker/scripts/install_service.sh --uninstall` |

The scheduler runs at fixed intervals only; time-of-day schedules and jobs sent from the Orchestrator are not supported yet.

---

## 4. CLI Reference

```text
usage: kinenix-worker [-h] [--version] {info,ping,run,watch,schedule,daemon} ...

positional arguments:
    info      Display worker machine hardware, architecture, and runtime stats
    ping      Check the connection and API key to the Orchestrator (KINENIX_ORCHESTRATOR_URL)
    run       Execute a flow or project bundle on this worker
    watch     Watch a directory and automatically trigger a flow when new files appear
    schedule  Execute a flow on a scheduled time interval
    daemon    Run multi-trigger daemon using a configuration file

options:
  --version, -v
```

### `kinenix-worker run` Options
- `flow_path`: Path to `flow.json` or project bundle directory.
- `--sandbox`: Execute inside an isolated temporary sandbox (`~/.kinenix/workspaces/<job_id>`).
- `--vars`: JSON string of variables to override.
- `--log-dir`: Also write a local JSON execution log to this directory. Telemetry to the Orchestrator does not depend on it.

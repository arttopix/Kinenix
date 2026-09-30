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
git clone -b dev https://github.com/arttopix/batautomate.git kinenix
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
```

### C. Run RPA Challenge Example Flow
```bash
kinenix-worker run flows/examples/rpachallenge/flow.json
```

To run inside an isolated sandbox directory:
```bash
kinenix-worker run flows/examples/rpachallenge/flow.json --sandbox
```

---

## 4. CLI Reference

```text
usage: kinenix-worker [-h] [--version] {info,run} ...

positional arguments:
  {info,run}
    info      Display worker machine hardware, architecture, and runtime stats
    run       Execute a flow or project bundle on this worker

options:
  --version, -v
```

### `kinenix-worker run` Options
- `flow_path`: Path to `flow.json` or project bundle directory.
- `--sandbox`: Execute inside an isolated temporary sandbox (`~/.kinenix/workspaces/<job_id>`).
- `--vars`: JSON string of variables to override.
- `--log-dir`: Custom path to store execution logs.

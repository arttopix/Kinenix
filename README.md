# kinenix

[![Status](https://img.shields.io/badge/Status-Active%20Development%20(WIP)-orange.svg?style=flat-square)](#)
[![CI](https://github.com/arttopix/Kinenix/actions/workflows/ci.yml/badge.svg)](https://github.com/arttopix/Kinenix/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/kinenix.svg?style=flat-square)](https://pypi.org/project/kinenix/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

> **Project Status: Active Development (Pre-Alpha / Work-in-Progress)**  
> kinenix is currently under rapid, active development. Core engine APIs, subflow execution specifications, and action schemas are evolving. It is not yet intended for mission-critical production deployments. Community feedback and contributions are warmly welcome!

> **Open-Source, Local AI-Native Agentic Automation Framework**  
> Next-generation Enterprise RPA powered by Python and on-device Small Language Models (SLMs). Eliminate commercial licensing overhead with autonomous agent workflows, zero-license Excel automation, and 100% free unattended robot workers.

---

## 1. Key Highlights & Core Philosophy

- **Local AI-Native Architecture:** Architected from the ground up for on-device Small Language Models (SLMs) running 100% locally on CPU (e.g., Qwen 2.5, Llama 3.2 via Ollama or GGUF). Powers structured extraction, AI decision steps, and plain-language failure diagnosis (self-healing selectors are planned) with zero API token costs and complete data privacy.
- **Zero-License Office Dependency:** No Microsoft 365 or Microsoft Excel installation required for spreadsheet operations. High-performance file-level processing is natively handled via `openpyxl` and `pandas`.
- **Business-First Mindset:** Telemetry and executive dashboards emphasize tangible business outcomes: Return on Investment (ROI), total hours saved, and cost reductions rather than pure technical stack traces.
- **Free Unlimited Unattended Workers:** Deploy robot worker daemons across any existing VMs, PCs, or edge devices with zero per-bot monthly licensing fees.
- **Python Power and Extensibility:** Clean plugin architecture (`BaseAction`) seamlessly integrating Web automation (Playwright), Excel/CSV, REST APIs, email, and AI models.

---

## 2. Modules

| Module | Role | Status |
| :--- | :--- | :--- |
| **`kinenix-core`** | Flow interpreter, action plugins, and `kinenix` CLI | Implemented |
| **`kinenix-worker`** | Unattended runner with schedule and file-watch triggers | Implemented (WebSocket dispatch planned) |
| **`kinenix-studio`** | Web-based flow editor and runner | In progress |
| **`kinenix-hub`** | Central telemetry server, dashboard, and AI failure summaries | Early |

Flows are packaged as self-contained project bundles under `flows/`. See [Architecture](docs/architecture.md) for the execution pipeline, AI integration, and target design, and [Roadmap](docs/roadmap.md) for delivery status.

---

## 3. Prerequisites

Before installing and running kinenix, ensure your system meets the following requirements:

### Core Requirements
| Component | Minimum Version | Notes |
| :--- | :--- | :--- |
| **Python** | `3.10` or higher | Recommended `3.10` - `3.12` with `pip` and `venv` |
| **Git** | `2.30+` | Required for version control and GitOps flow deployments |
| **Operating System** | Windows 10/11, Ubuntu 20.04+, Debian 11+, Raspberry Pi OS (64-bit), macOS 12+ | Fully cross-platform |

### Platform-Specific Setup

#### Linux / Ubuntu / Debian / Raspberry Pi (64-bit)
On Linux environments, ensure system packages and Playwright browser shared libraries are installed:
```bash
# 1. Install system packages and python venv
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv

# 2. Install Playwright Chromium with Linux system dependencies (libnss3, libasound2, etc.)
playwright install --with-deps chromium
```

#### Windows
Ensure Python 3.10+ is installed with **"Add python.exe to PATH"** checked. Install Playwright browser binaries with:
```powershell
kinenix install-browsers
# or: playwright install chromium
```

### Optional Dependencies
- **Local AI Inference (for `ai.prompt`, `ai.extract`):** Install [Ollama](https://ollama.com/) and run a local model:
  ```bash
  ollama run qwen2.5:1.5b
  ```
- **kinenix-studio Web UI Development:** [Node.js 18+](https://nodejs.org/) and `npm` (only required if developing or building `kinenix-studio/frontend`).

---

## 4. Quick Start

### Installation

#### From PyPI

Kinenix is published on PyPI as [`kinenix`](https://pypi.org/project/kinenix/), with the worker and the Hub as extras (from version 0.2.0b1; all packages share one version):

```bash
pip install kinenix              # core engine and the kinenix CLI
pip install "kinenix[worker]"    # plus kinenix-worker: unattended runs, schedules, cron
pip install "kinenix[hub]"       # plus kinenix-hub: central server and dashboard (`kinenix hub`)

kinenix install-browsers         # Playwright Chromium, needed for web actions
kinenix --version
```

Check the installation with the `hello` example (no browser needed), then start a project for your own task:

```bash
kinenix init demo --example hello    # copy an example; `kinenix init --list` shows the others
kinenix run demo                     # writes demo/output/greetings.csv

kinenix init "Get stock data"        # new project: describe the task in requirements.md,
                                     # then let an AI assistant write flow.md (see the AGENTS.md it creates)
```

The [Quickstart](docs/quickstart.md) walks through both, then a worker reporting to the Hub, in about ten minutes.

Kinenix Studio is not on PyPI yet; install it from source as shown below. Maintainers: see [docs/releasing.md](docs/releasing.md).

#### From source (all modules, for development)

Clone the repository and install the modules in editable mode within your Python virtual environment:

```bash
# Clone repository from dev branch
git clone -b dev https://github.com/arttopix/Kinenix.git kinenix
cd kinenix

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install core engine and worker daemon in editable mode
pip install -e ./kinenix-core -e ./kinenix-worker
# Optional: Studio and the Kinenix Hub
pip install -e ./kinenix-studio -e ./kinenix-hub
```

### Verification & Execution

```bash
# Check installed version and runtime info
kinenix version
kinenix-worker info

# List available flows (clean, deduplicated view)
kinenix list

# Run the RPA Challenge benchmark (auto-compiles flow.md if needed)
kinenix run rpachallenge

# Run with unattended worker daemon
kinenix-worker run flows/examples/rpachallenge/
```

---

## 5. Documentation

Start at the [documentation index](docs/README.md). Most used:

- **[Architecture](docs/architecture.md):** Modules, execution pipeline, AI integration, current vs. target design.
- **[Roadmap](docs/roadmap.md):** What is done, in progress, and next.
- **[Flow Markdown Specification](docs/flow_markdown_spec.md)** and **[Actions Reference](docs/actions_reference.md):** Writing flows.
- **[CLI Guide](docs/cli_guide.md)** and **[Hub Guide](docs/hub.md):** Running flows and the central server.

AI coding assistants should start at [AGENTS.md](AGENTS.md).

---

## 6. Acknowledgments

Kinenix is developed with the help of [Claude Code](https://claude.com/claude-code), Anthropic's AI coding assistant, which assists with code, tests, and documentation. The maintainer reviews and merges every change.

---

## 7. License

This project is licensed under the terms of the Open Source [MIT License](LICENSE).

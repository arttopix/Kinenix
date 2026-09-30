# CLI Execution Guide (kinenix)

This guide documents the Command Line Interface (CLI) for kinenix, powered by the `kinenix` runner in `kinenix-core`.

---

## 1. Installation

Install `kinenix` in editable mode within your Python virtual environment:

```powershell
cd kinenix-core
pip install -e .
```

Verify that the CLI is accessible:

```powershell
kinenix --version
# or
kinenix version
```

---

## 2. Core Commands

### 2.1 Check Version and Environment (`version`)
Outputs runtime details including kinenix version, Python runtime, operating system, and architecture:

```powershell
kinenix version
```

### 2.2 Install Playwright Browsers (`install-browsers`)
Downloads the Chromium browser binary required for Web automation tasks:

```powershell
kinenix install-browsers
```
*(Note: kinenix also detects missing browser binaries and automatically downloads Chromium on the first web flow execution).*

### 2.3 List Available Flows (`list`)
Scans the current workspace, `flows/`, `examples/`, and user cache directories to list all runnable workflows and project bundles:

```powershell
kinenix list
```

### 2.4 Run a Flow (`run`)
Executes an automation flow using the Smart Flow Resolver. You can specify a flow by alias, project folder, relative path, or absolute path:

```powershell
# Run by alias or bundle name
kinenix run rpachallenge

# Run by namespace
kinenix run examples/rpachallenge

# Run by direct file path
kinenix run flows/examples/rpachallenge/flow.json
```

---

## 3. Command Options & Parameters

### 3.1 Override / Inject Variables (`--vars`)
Pass external variables or runtime overrides to a flow as a JSON string:

```powershell
kinenix run rpachallenge --vars "{\"target_url\": \"https://rpachallenge.com/\"}"
```

Inside the flow, these variables can be accessed using the standard expression syntax `${target_url}`.

### 3.2 Custom Log Directory (`--log-dir`)
By default, Kinenix automatically detects the project root and writes structured JSON logs into `<project_root>/logs/`. You can override this location using `--log-dir`:

```powershell
kinenix run rpachallenge --log-dir "./custom_logs"
```

### 3.3 Send Telemetry to the Orchestrator (`--orchestrator`)
Uploads the execution log to a Central Orchestrator after the run. If the Orchestrator requires an API key, set `KINENIX_ORCHESTRATOR_API_KEY` first:

```powershell
$env:KINENIX_ORCHESTRATOR_API_KEY = "<key>"
kinenix run rpachallenge --orchestrator http://localhost:8080
```

See the [Central Orchestrator Guide](orchestrator.md#2-worker-authentication) for setup details.

---

## 4. Smart Flow Resolver Behavior

When running `kinenix run <input>`, the resolver searches candidate paths in the following priority order:

1. **Exact File Path:** Resolves directly if `<input>` is an existing file path.
2. **Project Bundle Directory:** If `<input>` is a directory containing `flow.json`, executes `<input>/flow.json`.
3. **Appended `.json`:** Checks if `<input>.json` exists.
4. **Discovered Flow Alias:** Matches aliases discovered by `kinenix list`.
5. **Project Search Directories:** Searches candidate subdirectories (`flows/`, `examples/`, `~/.kinenix/flows/`).

---

## 5. Running Automated Unit Tests

To run the automated test suite using `pytest`:

```powershell
cd kinenix-core
pytest tests
```

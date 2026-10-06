# CLI Execution Guide (kinenix)

This guide documents the Command Line Interface (CLI) for kinenix, powered by the `kinenix` runner in `kinenix-core`.

---

## 1. Installation

From PyPI (see the [Quickstart](quickstart.md)):

```powershell
pip install kinenix
```

From a clone of the repository, for development, in editable mode:

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

### 2.3 Start a Project (`init`)
Projects are created in your **flows folder**, separate from the Kinenix source code (default `~/kinenix-flows`; see [Where your flows live](quickstart.md#2-where-your-flows-live)). The first `kinenix init` at a terminal asks where it should be and whether to make it a git repository; scripts and CI use the default without asking. Every project in it runs by name from any folder.

**For a new task**, give it a name. The folder is derived from the name (`Get stock data` becomes `get_stock_data`; Thai names work):

```powershell
kinenix init "Get stock data"
kinenix init "Get stock data" --dir C:\bots\stocks     # choose the folder yourself
```

| Created file | Purpose |
| :--- | :--- |
| `requirements.md` | The requirements (RQ), with sections to fill in: goal, steps, changeable settings, secrets, output, errors, schedule |
| `AGENTS.md`, `CLAUDE.md` | Instructions for the AI assistant that turns `requirements.md` into `flow.md`: spec links, `kinenix actions`, config and secret rules, and `kinenix validate` before handing back |
| `flow.md`, `flow.json` | A one-step placeholder flow named after the task, so `validate` and `run` work from the start |
| `config/config.json` | Empty settings (`{}`) |
| `.env.example`, `.gitignore` | Where secrets go, and keeping `.env`, `output/`, and `logs/` out of git |
| `README.md` | The workflow: requirements, AI assistant, validate, run |

The intended workflow: write `requirements.md`, open the folder in an AI assistant and ask it to build the flow, then `kinenix validate` and `kinenix run`.

**To copy a complete example** instead, use `--example`. The folder must not exist or must be empty; nothing is overwritten.

```powershell
kinenix init --list                          # examples, and which need a browser
kinenix init demo --example hello            # no browser, no internet: the quickest installation check
kinenix init fx --example bot_fx_rate
kinenix run demo
```

| Example | What it does |
| :--- | :--- |
| `hello` | Builds a greeting table from `config.json` and writes a CSV; the quickest installation check |
| `bot_fx_rate` | Bank of Thailand transfer rates for chosen currencies and dates to CSV, with email (needs a browser) |
| `rpachallenge` | Fills the RPA Challenge form from an Excel file (needs a browser) |

The examples are copies of `flows/examples/` in the repository, kept identical by `.github/scripts/sync_examples.py` and a test.

### 2.4 Show or Change the Flows Folder (`flows-dir`)

```powershell
kinenix flows-dir                    # where flows are kept, and where that setting comes from
kinenix flows-dir D:\bots\flows      # change it (saved in ~/.kinenix/kinenix.env)
```

Order of precedence: the `KINENIX_FLOWS_DIR` environment variable, then the saved setting, then `~/kinenix-flows`.

### 2.5 List Actions and Their Parameters (`actions`)
Prints every action with the parameters it accepts, from the code itself. Useful while writing `flow.md`, and for AI assistants that need exact parameter names:

```powershell
kinenix actions          # all actions
kinenix actions web      # only web.*
```

### 2.6 List Available Flows (`list`)
Scans the current folder, your flows folder (`kinenix flows-dir`), and a repository's `flows/` and `examples/` folders, and lists every runnable flow and project bundle:

```powershell
kinenix list
```

### 2.7 Run a Flow (`run`)
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

### 3.3 Send Telemetry to the Hub (`--hub`)
Uploads the execution log to a Kinenix Hub after the run. If the Hub requires an API key, set `KINENIX_HUB_API_KEY` first:

```powershell
$env:KINENIX_HUB_API_KEY = "<key>"
kinenix run rpachallenge --hub http://localhost:8080
```

See the [Kinenix Hub Guide](hub.md#2-worker-authentication) for setup details.

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

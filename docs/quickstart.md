# Quickstart

From installation to your own task described in requirements, built with an AI assistant, and running unattended, in about ten minutes of reading. You need Python 3.10 or newer.

---

## 1. Install (1 minute)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install kinenix
kinenix --version
```

## 2. Where your flows live

Your flows are your own work, so Kinenix keeps them in **one folder of your own, separate from the Kinenix source code**. The first time you run `kinenix init`, it asks where; press Enter for the default:

| System | Default flows folder |
| :--- | :--- |
| Windows | `C:\Users\<you>\kinenix-flows` |
| Linux, Raspberry Pi | `/home/<you>/kinenix-flows` |
| macOS | `/Users/<you>/kinenix-flows` |

- It is a normal, visible folder, because you will open and review flows often. On Windows it is outside `Documents`, which OneDrive often syncs to the cloud.
- `kinenix init` offers to make it a **git repository**. Push it to a **private** repository (for example on GitHub) for history and backup: flows and their requirements often describe internal systems and business data.
- Every flow in it runs by name from any folder: `kinenix run <name>`. `kinenix list` shows them all.
- `kinenix flows-dir` shows the folder; `kinenix flows-dir PATH` changes it; the `KINENIX_FLOWS_DIR` environment variable overrides both (useful on servers).
- Do not keep your flows inside a clone of the Kinenix repository. Its `flows/examples` folder is for the examples that ship with Kinenix.

`~/.kinenix` is a different, hidden folder: it holds settings and data (`hub.env`, `hub.db`, `worker.env`), not flows.

## 3. Run a first flow (1 minute)

```bash
kinenix init my-bot --example hello
kinenix run my-bot
```

`--example hello` copies a small example into `my-bot` in your flows folder. It needs no browser and no internet, so it is the quickest check that everything works. Open `kinenix-flows/my-bot/output/greetings.csv` in your home folder:

```csv
Name,Greeting
Somchai,"Hello, Somchai!"
Malee,"Hello, Malee!"
Alex,"Hello, Alex!"
```

A JSON log of every step is saved under `logs/` (in the nearest git repository, otherwise in the folder you ran the command from; set `KINENIX_LOG_DIR` or `--log-dir` to choose).

## 4. Change it (2 minutes)

A project folder holds:

| File | What it is |
| :--- | :--- |
| `flow.md` | The flow, in readable Markdown. **This is the file you edit.** |
| `flow.json` | Build output of `flow.md`, rebuilt automatically before each run. Do not edit it. |
| `config/config.json` | Values the flow reads as `${config.*}`: names, paths, URLs, recipients. |

Try these:

1. **Different data, same flow:** change `names` in `config/config.json`, then `kinenix run my-bot`.
2. **Change the flow:** in `flow.md` step 1, add a field to the row, for example `"Team": "Kinenix"`, and add `"Team"` to `columns` in step 3. Run again.
3. **Catch mistakes before running:** misspell a parameter in `flow.md` (for example `colums` in step 3), then run `kinenix validate my-bot`. It names the step and suggests `columns`.
4. **See error handling:** set `"names": []`. Step 2 stops the flow with a clear business message instead of writing an empty file.

The syntax is in the [Flow Markdown specification](flow_markdown_spec.md); every action is in the [actions reference](actions_reference.md), and `kinenix actions` lists the parameters each one accepts.

## 5. Start your own task: requirements, then an AI assistant (3 minutes)

This is the normal way to build a flow in Kinenix. You describe the task; an AI assistant writes `flow.md`.

```bash
kinenix init "Get stock data"
```

This creates `get_stock_data` in your flows folder, with:

| File | What it is |
| :--- | :--- |
| `requirements.md` | Your requirements. Fill in the sections: goal, steps, settings that must be changeable, secrets, output, errors, schedule. |
| `AGENTS.md` (and `CLAUDE.md`) | Instructions for the AI assistant: follow the flow spec, check parameters with `kinenix actions`, put settings in `config/config.json` and secrets in `.env`, and run `kinenix validate` before handing back. |
| `flow.md` | A placeholder, to be replaced with the real steps. |
| `.env.example` | Names of the secrets the flow needs; copy to `.env`, which is never committed. |

Then:

1. Write `requirements.md`.
2. Open the folder in your AI assistant (for example Claude Code) and ask: *"Build the flow described in requirements.md."*
3. Review what it wrote, then:
   ```bash
   kinenix validate get_stock_data
   kinenix run get_stock_data
   ```

The `bot_fx_rate` example below was built this way: its README contains the original requirements.

## 6. Automate a website (2 minutes)

Web examples drive a real browser. Install it once per machine:

```bash
kinenix install-browsers
kinenix init --list                         # see the examples
kinenix init fx --example bot_fx_rate       # Bank of Thailand exchange rates to CSV
kinenix run fx
```

The browser opens, picks the currencies and dates on the Bank of Thailand site, reads one table per currency, and writes `output/Exchage_Rate.csv` in the `fx` project. Its email step runs in dry-run mode until you configure SMTP (see the README in the `fx` project).

## 7. Run unattended and watch it from a dashboard (2 minutes)

On the machine that runs flows (a server, a spare PC, or a Raspberry Pi):

```bash
pip install "kinenix[worker]"
kinenix-worker schedule --flow my-bot --cron "0 8 * * 1-5"   # 08:00 Monday to Friday
```

On the machine that collects results:

```bash
pip install "kinenix[hub]"
kinenix hub              # the first run asks a few questions; answer yes to accept other machines
kinenix hub show-key     # the key for workers
```

Point the worker at the Hub, then open the dashboard at `http://127.0.0.1:8080` on the Hub machine, or run `kinenix hub status`:

```bash
export KINENIX_HUB_URL=http://<hub-ip>:8080          # Windows: $env:KINENIX_HUB_URL = "..."
export KINENIX_HUB_API_KEY=<key from show-key>
kinenix-worker ping
```

---

## Where next

| Goal | Read |
| :--- | :--- |
| Write your own flows | [Flow Markdown specification](flow_markdown_spec.md), [actions reference](actions_reference.md) |
| Bundles, config, secrets in `.env`, subflows | [Project bundles](project_bundles.md) |
| All `kinenix` commands | [CLI guide](cli_guide.md) |
| Hub security, saved settings, the API | [Hub guide](hub.md) |
| Raspberry Pi worker as a service, cron triggers | [Worker guide](../kinenix-worker/README.md) |

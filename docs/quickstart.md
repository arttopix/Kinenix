# Quickstart

From installation to a flow running unattended, in about ten minutes. You need Python 3.10 or newer.

---

## 1. Install (1 minute)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install kinenix
kinenix --version
```

## 2. Create and run your first flow (2 minutes)

```bash
kinenix init my-bot
kinenix run my-bot
```

`kinenix init` copies the `hello` example into a new folder. It needs no browser and no internet. Open `my-bot/output/greetings.csv`:

```csv
Name,Greeting
Somchai,"Hello, Somchai!"
Malee,"Hello, Malee!"
Alex,"Hello, Alex!"
```

A JSON log of every step is saved under `logs/` (in the nearest git repository, otherwise in the folder you ran the command from; set `KINENIX_LOG_DIR` or `--log-dir` to choose).

## 3. Change it (3 minutes)

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

The syntax is in the [Flow Markdown specification](flow_markdown_spec.md); every action is in the [actions reference](actions_reference.md).

## 4. Automate a website (2 minutes)

Web examples drive a real browser. Install it once per machine:

```bash
kinenix install-browsers
kinenix init --list                         # see the examples
kinenix init fx --example bot_fx_rate       # Bank of Thailand exchange rates to CSV
kinenix run fx
```

The browser opens, picks the currencies and dates on the Bank of Thailand site, reads one table per currency, and writes `fx/output/Exchage_Rate.csv`. Its email step runs in dry-run mode until you configure SMTP (see `fx/README.md`).

## 5. Run unattended and watch it from a dashboard (2 minutes)

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

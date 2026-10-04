# BOT FX Transfer Rate Collector

Collects historical buying transfer rates from the Bank of Thailand, writes them to a CSV file grouped by currency, and emails the file.

## Requirement

1. Open https://www.bot.or.th/en/statistics/exchange-rate.html.
2. Read the Historical Foreign Exchange Rates table.
3. Select the currencies USD, GBP, SGD, JPY, EUR and collect the transfer rate from 01-12-2024 to 31-12-2024.
4. Write the transfer rates to `Exchage_Rate.csv`, grouped by currency. (The original requirement asks for an Excel file; CSV is used because Excel is not installed. CSV opens in Excel, Google Sheets, or any text editor.)
5. Email the CSV file to the recipient list.

The URL, currency list, dates, file paths, and email recipients are variables in `config/config.json`, so changing them never requires editing the flow. Exceptions must be handled.

## How the flow works

| Step | What it does |
| :--- | :--- |
| 1-2 | Opens the page (retried twice) and accepts the cookie banner if it appears |
| 3-5 | Opens the currency filter and ticks each currency in `currencies` |
| 6-13 | Picks the start and end dates in the date pickers (year, month, then day) |
| 14-15 | Presses GO and waits for the result tables |
| 16 | For each currency: opens its tab, reads the visible table with `web.get_table`, keeps Date and Buying Rates Transfer as numbers, and adds a Currency column |
| 17 | Writes all rows to the CSV in currency order: Currency, Date, Buying Transfer Rate |
| 18-19 | Saves a result screenshot and closes the browser |
| 20 | Emails the CSV with `email.send` (Gmail SMTP) |

## Configuration (`config/config.json`)

| Key | Example | Purpose |
| :--- | :--- | :--- |
| `url` | BOT exchange rate page | Page to open |
| `currencies` | `["USD", "GBP", "SGD", "JPY", "EUR"]` | Currencies to select and their order in the CSV |
| `start_date`, `end_date` | `{"day": "1", "month": "December", "year": "2024"}` | Date range, as shown in the site's date picker |
| `output_path` | `./output/Exchage_Rate.csv` | Output CSV file, relative to this bundle |
| `screenshot_path`, `error_dir` | `./output/...` | Result screenshot and automatic failure screenshots |
| `headless` | `false` | `false` shows the browser window; machines without a display switch to headless automatically |
| `email.to` | `["someone@example.com"]` | Recipient list |
| `email.subject`, `email.body` | | Message text |
| `email.dry_run` | `true` | `true` checks the email without sending it |

## Sending the email

Email is sent through Gmail SMTP and needs an app password, read from the environment, never from the config:

```powershell
$env:GMAIL_USER = "you@gmail.com"
$env:GMAIL_APP_PASSWORD = "<16-character app password>"
```

Then set `email.dry_run` to `false` in `config/config.json`.

## Run

```powershell
kinenix run flows/examples/bot_fx_rate
kinenix-worker run flows/examples/bot_fx_rate
```

## Error handling

| Situation | Behavior |
| :--- | :--- |
| Page slow or unreachable | `web.open` retries twice, 5 seconds apart |
| No cookie banner | Skipped (`optional`) |
| Currency not offered by the site | Fails at "Tick Currency Checkbox" after 10 seconds |
| GO button or table read flaky | Retried twice |
| Table empty or a column renamed by the site | `web.get_table` fails with the actual headers (`min_rows`, `columns`) |
| CSV file locked (open in another program) | Retried twice, then fails |
| Email fails | Retried twice, 10 seconds apart |
| Any failure | A screenshot is saved in `output/errors/`, and the Orchestrator receives the failed step and error |
| `config.json` missing or `url` empty | Fails at step 1 instead of continuing on a blank page |

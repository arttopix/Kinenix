# BOT FX Transfer Rate Collector

Collects one month of historical buying transfer rates from the Bank of Thailand (the previous month by default), writes them to a CSV file grouped by currency, and emails the file. Scheduled on the 1st of each month, it reports the month that just ended.

## Requirement

1. Open https://www.bot.or.th/en/statistics/exchange-rate.html.
2. Read the Historical Foreign Exchange Rates table.
3. Select the currencies USD, GBP, SGD, JPY, EUR and collect the transfer rate for one month. (The original requirement names 01-12-2024 to 31-12-2024; the month is now a setting, see `month` below.)
4. Write the transfer rates to `Exchage_Rate.csv`, grouped by currency. (The original requirement asks for an Excel file; CSV is used because Excel is not installed. CSV opens in Excel, Google Sheets, or any text editor.)
5. Email the CSV file to the recipient list.

The URL, currency list, report month, file paths, and email recipients are variables in `config/config.json`, so changing them never requires editing the flow. Exceptions must be handled.

## How the flow works

| Step | What it does |
| :--- | :--- |
| 1-2 | Works out the first and last day of the report month with `date.calc` |
| 3-4 | Opens the page (retried twice) and accepts the cookie banner if it appears |
| 5-7 | Opens the currency filter and ticks each currency in `currencies` |
| 8-15 | Picks the start and end dates in the date pickers (year, month name, then day) |
| 16-17 | Presses GO and waits for the result tables |
| 18 | For each currency: opens its tab, reads the visible table with `web.get_table`, keeps Date and Buying Rates Transfer as numbers, and adds a Currency column |
| 19 | Writes all rows to the CSV in currency order: Currency, Date, Buying Transfer Rate |
| 20-21 | Saves a result screenshot and closes the browser |
| 22 | Emails the CSV with `email.send` (Gmail SMTP) |

## Configuration (`config/config.json`)

| Key | Example | Purpose |
| :--- | :--- | :--- |
| `url` | BOT exchange rate page | Page to open |
| `currencies` | `["USD", "GBP", "SGD", "JPY", "EUR"]` | Currencies to select and their order in the CSV |
| `month` | `{"date": "today", "add_months": -1}` | Report month: the month of `date` moved by `add_months`. The default is the previous month. For a fixed month, give any day in it, for example `{"date": "2024-12-01", "add_months": 0}` for December 2024 |
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
| Any failure | A screenshot is saved in `output/errors/`, and the Hub receives the failed step and error |
| `config.json` missing or `url` empty | Fails at step 1 instead of continuing on a blank page |

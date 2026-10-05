# BOT FX Transfer Rate Collector
> Description: Collect Bank of Thailand historical buying transfer rates for the configured currencies and date range, write them to a CSV file grouped by currency, and email the file.
> Version: 1.0.0

## Variables
- `fx_rows`: []

## Steps

### 1. Open BOT Exchange Rate Page (`web.open`)
- **url:** `${config.url}`
- **headless:** `${config.headless}`
- **timeout:** 60000
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5.0

### 2. Accept Cookie Banner (`web.click`)
- **selector:** `button:has-text('Accept recommended cookies')`
- **timeout:** 15000
- **optional:** true

### 3. Open Currency Filter (`web.click`)
- **selector:** `#dropdownCurrency`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 2.0

### 4. Select Configured Currencies (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Tick Currency Checkbox (`web.check`):
    - **selector:** `.currency-filter input[name='currencyCheck'][value='${currency}']`
    - **timeout:** 10000

### 5. Close Currency Filter (`web.click`)
- **selector:** `h3:has-text('Historical Foreign Exchange Rates')`

### 6. Open Start Date Picker (`web.click`)
- **selector:** `.date-filter input[placeholder='Select a date'] >> nth=0`

### 7. Choose Start Year (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=1`
- **value:** `${config.start_date.year}`

### 8. Choose Start Month (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=0`
- **text:** `${config.start_date.month}`

### 9. Choose Start Day (`web.click`)
- **selector:** `.react-datepicker__day:not(.react-datepicker__day--outside-month):text-is('${config.start_date.day}')`

### 10. Open End Date Picker (`web.click`)
- **selector:** `.date-filter input[placeholder='Select a date'] >> nth=1`

### 11. Choose End Year (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=1`
- **value:** `${config.end_date.year}`

### 12. Choose End Month (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=0`
- **text:** `${config.end_date.month}`

### 13. Choose End Day (`web.click`)
- **selector:** `.react-datepicker__day:not(.react-datepicker__day--outside-month):text-is('${config.end_date.day}')`

### 14. Search Historical Rates (`web.click`)
- **selector:** `button.historical-btn`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 3.0

### 15. Wait For Results To Load (`logic.delay`)
- **seconds:** 3

### 16. Read Transfer Rates Per Currency (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Show Currency Table (`web.click`):
    - **selector:** `.main-content:has(button.historical-btn) button:text-is('${currency}')`
    - **timeout:** 10000
  - Read Currency Table (`web.get_table`):
    - **selector:** `.main-content:has(button.historical-btn) table:visible`
    - **columns:** {"Period": "Date", "Buying Rates Transfer": "Buying Transfer Rate"}
    - **numeric_columns:** ["Buying Transfer Rate"]
    - **add_columns:** {"Currency": "${currency}"}
    - **min_rows:** 1
    - **timeout:** 15000
    - **output_var:** `currency_rows`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 2.0
  - Collect Currency Rows (`logic.append`):
    - **target:** `fx_rows`
    - **item:** `${currency_rows}`
    - **extend:** true

### 17. Write Grouped Rates To CSV (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `${fx_rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 2.0

### 18. Capture Result Screenshot (`web.screenshot`)
- **path:** `${config.screenshot_path}`
- **on_error:** continue

### 19. Close Browser (`web.close`)
- **on_error:** continue

### 20. Email CSV Report (`email.send`)
- **to:** `${config.email.to}`
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **attachments:** ["${config.output_path}"]
- **dry_run:** `${config.email.dry_run}`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 10.0

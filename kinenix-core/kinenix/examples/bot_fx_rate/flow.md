# BOT FX Transfer Rate Collector
> Description: Collect Bank of Thailand historical buying transfer rates for the configured currencies over one month (the previous month by default), write them to a CSV file grouped by currency, and email the file.
> Version: 1.0.0

## Variables
- `fx_rows`: []

## Steps

### 1. First Day Of Report Month (`date.calc`)
- **date:** `${config.month.date}`
- **add_months:** `${config.month.add_months}`
- **snap:** start_of_month
- **output_var:** `start`

### 2. Last Day Of Report Month (`date.calc`)
- **date:** `${config.month.date}`
- **add_months:** `${config.month.add_months}`
- **snap:** end_of_month
- **output_var:** `end`

### 3. Open BOT Exchange Rate Page (`web.open`)
- **url:** `${config.url}`
- **headless:** `${config.headless}`
- **timeout:** 60000
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5.0

### 4. Accept Cookie Banner (`web.click`)
- **selector:** `button:has-text('Accept recommended cookies')`
- **timeout:** 15000
- **optional:** true

### 5. Open Currency Filter (`web.click`)
- **selector:** `#dropdownCurrency`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 2.0

### 6. Select Configured Currencies (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Tick Currency Checkbox (`web.check`):
    - **selector:** `.currency-filter input[name='currencyCheck'][value='${currency}']`
    - **timeout:** 10000

### 7. Close Currency Filter (`web.click`)
- **selector:** `h3:has-text('Historical Foreign Exchange Rates')`

### 8. Open Start Date Picker (`web.click`)
- **selector:** `.date-filter input[placeholder='Select a date'] >> nth=0`

### 9. Choose Start Year (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=1`
- **value:** `${start.year}`

### 10. Choose Start Month (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=0`
- **text:** `${start.month_name}`

### 11. Choose Start Day (`web.click`)
- **selector:** `.react-datepicker__day:not(.react-datepicker__day--outside-month):text-is('${start.day}')`

### 12. Open End Date Picker (`web.click`)
- **selector:** `.date-filter input[placeholder='Select a date'] >> nth=1`

### 13. Choose End Year (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=1`
- **value:** `${end.year}`

### 14. Choose End Month (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=0`
- **text:** `${end.month_name}`

### 15. Choose End Day (`web.click`)
- **selector:** `.react-datepicker__day:not(.react-datepicker__day--outside-month):text-is('${end.day}')`

### 16. Search Historical Rates (`web.click`)
- **selector:** `button.historical-btn`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 3.0

### 17. Wait For Results To Load (`logic.delay`)
- **seconds:** 3

### 18. Read Transfer Rates Per Currency (`logic.loop`)
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

### 19. Write Grouped Rates To CSV (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `${fx_rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 2.0

### 20. Capture Result Screenshot (`web.screenshot`)
- **path:** `${config.screenshot_path}`
- **on_error:** continue

### 21. Close Browser (`web.close`)
- **on_error:** continue

### 22. Email CSV Report (`email.send`)
- **to:** `${config.email.to}`
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **attachments:** ["${config.output_path}"]
- **dry_run:** `${config.email.dry_run}`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 10.0

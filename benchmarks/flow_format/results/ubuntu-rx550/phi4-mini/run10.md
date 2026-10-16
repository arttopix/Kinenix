```markdown
# Collect Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `name`: `${config.month.date}`
- `headless`: `${config.headless}`
- `output_path`: `${config.output_path}`
- `email.to`: `${config.email.to}`
- `email.subject`: `${config.email.subject}`
- `email.body`: `${config.email.body}`
- `email.dry_run`: `${config.email.dry_run}`

## Steps

### 1. Calculate the first and last day of the report month (`date.calc`)
- **date:** `${config.month.date}`
- **add_months:** `-1`
- **input_format:** `YYYY-MM-DD`
- **snap:** `true`
- **output_var:** `first_last_date`
- **on_error:** retry
- **max_retries:** 2

### 2. Open the Bank of Thailand website (`web.open`)
- **url:** `${config.url}`
- **headless:** `${config.headless}`
- **timeout:** `30`
- **output_var:** `page_opened`
- **on_error:** retry
- **max_retries:** 2

### 3. Accept cookie banner (`web.click`)
- **selector:** `.cookie-banner-button`
- **label:** 'Accept recommended cookies'
- **on_error:** retry
- **max_retries:** 2

### 4. Open the currency filter (`web.open`)
- **url:** `${config.url}`
- **headless:** `${config.headless}`
- **timeout:** `30`
- **output_var:** `currency_filter_opened`
- **on_error:** retry
- **max_retries:** 2

### 5. Tick each currency in the filter (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Filter (`web.click`):
    - **selector:** `#dropdownCurrency`
    - **label:** `null`
    - **on_error:** retry
    - **max_retries:** 2
  - Uncheck All (`web.uncheck`):
    - **selector:** `.currency-filter input[name='currencyCheck']`
    - **label:** `null`
    - **on_error:** retry
    - **max_retries:** 2
  - Check Each Currency (`web.check`):
    - **selector:** `.currency-filter input[name='currencyCheck'][value='${currency}']`
    - **label:** `null`
    - **on_error:** retry
    - **max_retries:** 2

### 6. Pick the start and end dates in the date picker (`web.get_text`)
- **selector:** `.react-datepicker select >> nth=1`
- **label:** `Year`
- **output_var:** `start_year`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Set Year (`web.type`):
    - **selector:** `.react-datepicker select >> nth=1`
    - **text:** `${start_year}`
- **Sub-steps:**
  - Pick Month (`web.get_text`)
    - **selector:** `.react-datepicker select >> nth=0`
    - **label:** `Month`
    - **output_var:** `start_month`
    - **on_error:** retry
    - **max_retries:** 2
  - Set Month (`web.type`)
    - **selector:** `.react-datepicker select >> nth=0`
    - **text:** `${start_month}`
- **Sub-steps:**
  - Pick Day (`web.get_text`)
    - **selector:** `.react-datepicker month .day-cell:nth(:n)`
    - **label:** `Day`
    - **output_var:** `start_day`
    - **on_error:** retry
    - **max_retries:** 2
- **Sub-steps:**
  - Set Day (`web.type`)
    - **selector:** `.react-datepicker month .day-cell:nth(:n)`
    - **text:** `${start_day}`
- **Sub-steps:**
  - Pick Year (`web.get_text`)
    - **selector:** `.react-datepicker select >> nth=1`
    - **label:** `Year`
    - **output_var:** `end_year`
    - **on_error:** retry
    - **max_retries:** 2
  - Set Year (`web.type`)
    - **selector:** `.react-datepicker select >> nth=1`
    - **text:** `${end_year}`
- **Sub-steps:**
  - Pick Month (`web.get_text`)
    - **selector:** `.react-datepicker select >> nth=0`
    - **label:** `Month`
    - **output_var:** `end_month`
    - **on_error:** retry
    - **max_retries:** 2
  - Set Month (`web.type`)
    - **selector:** `.react-datepicker select >> nth=0`
    - **text:** `${end_month}`
- **Sub-steps:**
  - Pick Day (`web.get_text`)
    - **selector:** `.react-datepicker month .day-cell:nth(:n)`
    - **label:** `Day`
    - **output_var:** `end_day`
    - **on_error:** retry
    - **max_retries:** 2
  - Set Day (`web.type`)
    - **selector:** `.react-datepicker month .day-cell:nth(:n)`
    - **text:** `${end_day}`

### 7. Click 'button.historical-btn' to search (`web.click`)
- **selector:** `button.historical-btn`
- **label:** `null`
- **on_error:** retry
- **max_retries:** 2

### 8. Read the table for each currency (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Open Currency Tab (`web.click`)
    - **selector:** `text=currency`
    - **label:** `null`
    - **on_error:** retry
    - **max_retries:** 2
  - Get Table (`web.get_table`)
    - **selector:** `.buying-transfer-rates-table`
    - **columns:** `{"Period": "Date", "Buying Rates Transfer": "Buying Transfer Rate", "Currency": "Currency"}`
    - **min_rows:** `2`
    - **output_var:** `table_data`
    - **on_error:** retry
    - **max_retries:** 2
  - Append Data (`csv.write`)
    - **file_path:** `${output_path}`
    - **data:** `["Currency", "Date", "Buying Transfer Rate"] + ${table_data}`
    - **on_error:** retry
    - **max_retries:** 2

### 9. Close the browser (`web.close`)
- **output_var:** `page_closed`
- **on_error:** continue
- **max_retries:** 2

### 10. Email the CSV to the specified address (`email.send`)
- **to:** `${config.email.to}`
- **cc:** `null`
- **bcc:** `null`
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **html:** `false`
- **attachments:** `["${output_path}"]`
- **smtp_host:** `null`
- **smtp_port:** `null`
- **smtp_user:** `null`
- **smtp_password:** `null`
- **use_tls:** `false`
- **dry_run:** `${config.email.dry_run}`
- **on_error:** retry
- **max_retries:** 2

### 11. Retry if any step fails (`flow.fail`)
- **message:** `${on_error}`
- **category:** `critical`
```
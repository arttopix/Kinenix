```markdown
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `date_start`: <first day of the report month>
- `date_end`: <last day of the report month>
- `currencies`: <comma-separated list of currencies>
- `output_path`: <path to save CSV>
- `email_to`: <recipient's email>
- `email_subject`: <email subject>
- `email_body`: <email body>
- `screenshot_path`: <path for screenshots>

## Steps

### 1. Calculate Report Month (`date.calc`)
- **date:** `config.month.date`
- **input_format:** `%Y-%m-%d`
- **add_months:** `-1`
- **output_var:** `date_start`
- **output_format:** `%Y-%m-%d`

### 2. Open Bank of Thailand Website (`web.open`)
- **url:** `${config.url}`
- **headless:** `<true/false>`
- **output_var:** `page`
- **on_error:** retry
- **max_retries:** 2

### 3. Accept Cookies (`web.click`)
- **selector:** <cookie accept button selector>
- **label:** 'Accept recommended cookies'
- **output_var:** `cookies_accepted`

### 4. Select Currencies (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`logic.if`):
    - **condition:** `cookies_accepted`
    - **left:** `true`
    - **right:** `false`
    - **Sub-steps:**
      - Uncheck Currency (`web.uncheck`):
        - **selector:** `<currency filter checkbox>`
        - **label:** `${currency}`
      - Check Currency (`web.click`):
        - **selector:** `<currency filter checkbox>`
        - **label:** `${currency}`
- **on_error:** retry
- **max_retries:** 2

### 5. Set Date Range (`logic.loop`)
- **items:** `date_start, date_end`
- **item_var:** `date`
- **Sub-steps:**
  - Set Year (`date.pick_year`):
    - **selector:** `.react-datepicker select >> nth=1`
    - **output_var:** `year`
  - Set Month (`date.pick_month`):
    - **selector:** `.react-datepicker select >> nth=0`
    - **output_var:** `month`
  - Set Day (`date.pick_day`):
    - **selector:** `<day cell text>`
    - **output_var:** `day`
  - Set Date Range (`date.set_range`):
    - **target:** `year, month, day`
    - **output_var:** `date_range`
- **on_error:** retry
- **max_retries:** 2

### 6. Search Historical Data (`web.click`)
- **selector:** `.button.historical-btn`
- **output_var:** `search_complete`

### 7. Collect Currency Data (`logic.loop`)
- **items:** `currencies`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`):
    - **selector:** `<currency tab button>`
    - **label:** `${currency}`
  - Get Currency Data (`web.get_table`):
    - **selector:** `<currency data table>`
    - **columns:** `{"Period": "Date", "Buying Rates Transfer": "Buying Transfer Rate"}`
    - **add_columns:** `{"Currency": "Currency"}`
    - **min_rows:** 1
    - **output_var:** `currency_data`
- **on_error:** retry
- **max_retries:** 2

### 8. Write Data to CSV (`csv.write`)
- **file_path:** `output_path`
- **data:** `<currency_data>`
- **columns:** `{"Currency", "Date", "Buying Transfer Rate"}`
- **on_error:** retry
- **max_retries:** 2

### 9. Close Browser (`web.close`)

### 10. Send Email (`email.send`)
- **to:** `<email_to>`
- **cc:** `<cc>`
- **bcc:** `<bcc>`
- **subject:** `<email_subject>`
- **body:** `<email_body>`
- **html:** `<false/true>`
- **attachments:** `<false/true>`
- **smtp_host:** `<smtp_host>`
- **smtp_port:** `<smtp_port>`
- **smtp_user:** `<smtp_user>`
- **smtp_password:** `<smtp_password>`
- **use_tls:** `<true/false>`
- **dry_run:** `<true/false>`
- **on_error:** retry
- **max_retries:** 2
```
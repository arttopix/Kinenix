# Collect Bank of Thailand Buying Transfer Rates for Currencies over One Month

## Variables
- `config.month`: {}
- `config.currencies`: []
- `config.url`: "https://api.bankofthailand.com/forex"
- `config.output_path`: "results/"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Currency Buying Transfer Rates"
- `config.email.body`: "This is a test email body."
- `config.email.dry_run`: false
- `headless`: false
- `max_retries`: 2
- `retry_interval`: 30

## Steps

### 1. Calculate First and Last Day of the Month
- **output_var:** `first_day`
- **output_var:** `last_day`
- **logic.delay:** 30
- **Sub-steps:**
  - Calculate First Day (`date.calc`):
    - **date:** "2023-01-01"
    - **add_days:** 1
    - **output_var:** `first_day`
  - Calculate Last Day (`date.calc`):
    - **date:** "2023-12-31"
    - **add_days:** 1
    - **output_var:** `last_day`

### 2. Open URL and Accept Cookie
- **output_var:** `page`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Open URL (`web.open`):
    - **url:** `${config.url}`
    - **headless:** ${headless}
    - **timeout:** 5
  - Accept Cookie Banner (`web.is_visible`):
    - **selector:** ".cookie-banner"
    - **timeout:** 5

### 3. Filter Currency and Select Start and End Dates
- **output_var:** `currency_list`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Filter Currencies (`web.select_option`):
    - **selector:** "#dropdownCurrency"
    - **value:** "${config.currencies}"
    - **text:** "${config.currencies[0]}"
    - **timeout:** 10
  - Select Start Date (`web.type`):
    - **selector:** "#react-datepicker--startMonth"
    - **input_format:** "MM/DD/YYYY"
    - **value:** "${first_day}"
    - **timeout:** 10
  - Select End Date (`web.type`):
    - **selector:** "#react-datepicker--endMonth"
    - **input_format:** "MM/DD/YYYY"
    - **value:** "${last_day}"
    - **timeout:** 10

### 4. Search for Historical Data
- **output_var:** `historical_data`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Click Search Button (`web.click`):
    - **selector:** "#historical-btn"
    - **timeout:** 10

### 5. Collect Data for Each Currency
- **output_var:** `currency_data`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Loop Through Currencies (`logic.loop`):
    - **items:** `${config.currencies}`
    - **item_var:** `currency`
    - **Sub-steps:**
      - Select Currency Tab (`web.select_option`):
        - **selector:** "#dropdownCurrency"
        - **value:** "${currency}"
        - **timeout:** 10
      - Read Table Data (`web.get_table`):
        - **selector:** "#historical-table"
        - **columns:** "Date" "Buying Transfer Rate"
        - **numeric_columns:** true
        - **timeout:** 10
        - **output_var:** `table_data`
      - Write Data to CSV (`csv.write`):
        - **file_path:** "${config.output_path}${currency}.csv"
        - **data:** `${table_data}`
        - **append:** true

### 6. Close Browser and Email CSV
- **output_var:** `email_data`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Close Browser (`web.close`):
    - **timeout:** 10
  - Send Email (`email.send`):
    - **to:** `${config.email.to}`
    - **cc:** ""
    - **bcc:** ""
    - **subject:** "${config.email.subject}"
    - **body:** "${config.email.body}"
    - **html:** false
    - **attachments:** []
    - **smtp_host:** ""
    - **smtp_port:** ""
    - **smtp_user:** ""
    - **smtp_password:** ""
    - **use_tls:** false
    - **dry_run:** ${config.email.dry_run}

### 7. Clean Up and Retry
- **output_var:** `retry_count`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Check Retry Count (`logic.append`):
    - **target:** `retry_count`
    - **item:** "1"
  - Retry (`logic.delay`):
    - **seconds:** 60
    - **on_error:** retry
    - **max_retries:** 2

### Final Step: Write Flow
- **output_var:** `flow`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Write Flow (`flow.write`):
    - **file_path:** "flow.json"
    - **data:** `${flow}`

## Result Variables
- `flow`: The final flow object with all steps.
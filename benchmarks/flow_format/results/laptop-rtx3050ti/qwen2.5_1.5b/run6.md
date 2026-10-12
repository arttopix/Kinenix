# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: {}
- `config.url`: "https://www.bangkokbank.com/th/transfer/bank-rate"
- `config.currencies`: ["THB", "USD", "EUR", "JPY", "CNY"]
- `config.month`: {"date": "today", "add_months": -1}
- `config.output_path`: "path/to/output/bank-rate.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates"
- `config.email.body`: "Hi there, please find the collected bank rates attached."
- `config.email.dry_run`: false
- `config.headless`: false
- `config.retry`:
  - `url`: "https://www.bangkokbank.com/th/transfer/bank-rate"
  - `retry_interval`: 5
  - `max_retries`: 5

## Steps

### 1. Get Month and First/Last Day (`http.request`)
- **url:** "https://www.bangkokbank.com/th/transfer/bank-rate"
- **method:** GET
- **timeout:** 10
- **output_var:** `config.month`

### 2. Open URL and Accept Cookies (`web.open`)
- **url:** `${config.url}`
- **headless:** ${config.headless}
- **timeout:** 10

### 3. Filter Currency Dropdown (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **value:** ${config.currencies}
- **input_var:** `currency_option`
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `currency_option`

### 4. Select Start and End Dates (`web.select_option`)
- **selector:** ".react-datepicker"
- **value:** ${config.month.date}, ${config.month.add_months}
- **input_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `start_date`

### 5. Click Search Button (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **timeout:** 5

### 6. Loop Through Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **output_var:** `currency`

### 7. Open Currency Page and Select (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **input_var:** `currency_option`
- **value:** ${currency}
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `currency_option`

### 8. Open Date Picker (`web.select_option`)
- **selector:** ".react-datepicker"
- **input_var:** `start_date`
- **value:** ${start_date}
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `start_date`

### 9. Open Date Picker (`web.select_option`)
- **selector:** ".react-datepicker"
- **input_var:** `end_date`
- **value:** ${start_date}
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `end_date`

### 10. Read Table (`web.get_table`)
- **selector:** ".table"
- **label:** "table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **min_rows:** 10
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `data`

### 11. Write CSV to Path (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `${data}`
- **on_error:** retry
- **max_retries:** 2
- **output_var:** `csv_output`

### 12. Close Browser (`web.close`)
- **timeout:** 5

### 13. Email CSV (`email.send`)
- **to:** `${config.email.to}`
- **cc:** "cc@example.com"
- **bcc:** "bcc@example.com"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** false
- **attachments:** false
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** false
- **dry_run:** ${config.dry_run}

### 14. Retry if Failed (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **output_var:** `currency`
- **Sub-steps:**
  - `1. Open URL and Accept Cookies`
  - `2. Filter Currency Dropdown`
  - `3. Select Start and End Dates`
  - `4. Click Search Button`
  - `5. Loop Through Currencies`
  - `6. Open Currency Page and Select`
  - `7. Open Date Picker`
  - `8. Open Date Picker`
  - `9. Read Table`
  - `10. Write CSV to Path`
  - `11. Close Browser`
  - `12. Email CSV`
  - `13. Retry if Failed`

### 15. Finalize (`flow.return`)
- **value:** "Flow completed successfully."
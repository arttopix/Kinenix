# Collect Bank of Thailand Buying Transfer Rates for Several Currencies and Email as CSV

## Variables
- `config.url`: "https://www.bankofthailand.org.th/"
- `config.currencies`: ["THB", "USD", "EUR", "JPY"]
- `config.month.date`: "today"
- `config.month.add_months`: -1
- `config.output_path`: "output/bank_of_thailand_rates.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates"
- `config.email.body`: "This is an automated email with Bank of Thailand buying transfer rates."

## Steps

### 1. Get Month and Year (`http.request`)
- **url:** `${config.url}`
- **method:** "GET"
- **headers:** {}
- **payload:** {}
- **timeout:** 30

### 2. Open URL and Accept Cookie Banner (`web.open`)
- **url:** `${config.url}`
- **headless:** false
- **timeout:** 60

### 3. Filter Currencies (`web.select_option`)
- **selector:** ".dropdownCurrency"
- **value:** "${config.currencies}"
- **text:** "Select Currency"
- **label:** "Filter"
- **timeout:** 30

### 4. Open Date Picker (`web.open`)
- **selector:** "input[type='date']"
- **label:** "Pick Date"
- **timeout:** 30

### 5. Select Start and End Dates (`web.select_option`)
- **selector:** ".react-datepicker__header"
- **value:** "start_date"
- **text:** "Start Date"
- **label:** "Date"
- **timeout:** 30
- **input_format:** "MM/DD/YYYY"
- **add_days:** -1
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 6. Select End Date (`web.select_option`)
- **selector:** ".react-datepicker__header"
- **value:** "end_date"
- **text:** "End Date"
- **label:** "Date"
- **timeout:** 30
- **input_format:** "MM/DD/YYYY"
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 7. Click "Historical Rate" Button (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Historical Rate"
- **timeout:** 30

### 8. Scroll to "Buy Rate" (`web.scroll`)
- **selector:** ".buy-rate"
- **direction:** "down"
- **amount:** 150
- **timeout:** 30

### 9. Read Table Headers and Data (`web.get_table`)
- **selector:** "table"
- **label:** "Buy Rate"
- **columns:** "Date", "Buying Rates Transfer"
- **numeric_columns:** true
- **min_rows:** 1
- **timeout:** 30

### 10. Extract Data and Write to CSV (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** "${table_data}"
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 11. Close Browser (`web.close`)
- **selector:** "body"
- **timeout:** 30

### 12. Send Email (`email.send`)
- **to:** `${config.email.to}`
- **cc:** ""
- **bcc:** ""
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **html:** ""
- **attachments:** []
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** true
- **dry_run:** false
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 13. Retry Opening Page and Searching Twice (`logic.delay`)
- **seconds:** 5

### 14. Retry Writing CSV Twice (`logic.delay`)
- **seconds:** 5

### 15. Retry Screenshot (`logic.delay`)
- **seconds:** 5

### 16. Retry Email (`logic.delay`)
- **seconds:** 5
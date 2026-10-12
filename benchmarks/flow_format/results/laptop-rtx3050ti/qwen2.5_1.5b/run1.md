# Collect Bank of Thailand Buying Transfer Rates for One Month

## Variables
- `month`: {"date": "today", "add_months": -1}
- `currencies`: ["THB", "USD", "JPY", "EUR", "GBP", "AUD", "CAD", "CHF", "DKK", "INR"]
- `output_path`: "/path/to/output.csv"
- `config_url`: "https://www.bangkokbank.com/currency"
- `config_currencies`: ["USD", "JPY", "EUR", "GBP", "AUD", "CAD", "CHF", "DKK", "INR"]
- `config_month`: {"date": "today", "add_months": -1}
- `config_email`: {"to": "example@example.com", "subject": "Bank of Thailand Buying Transfer Rates Report", "dry_run": false}
- `config_email_subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config_email_body`: "This is a test email."
- `config_email_to`: "example@example.com"
- `config_email_dry_run`: false
- `config_email`: {"to": "example@example.com", "subject": "Bank of Thailand Buying Transfer Rates Report", "dry_run": false}
- `config_email_subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config_email_body`: "This is a test email."
- `config_email_to`: "example@example.com"
- `config_email_dry_run`: false

## Steps

### 1. Open ${config_url}
- **web.open**
  - **url:** "${config_url}"
  - **headless:** true

### 2. Open Currency Filter
- **web.select_option**
  - **selector:** "#dropdownCurrency"
  - **value:** "USD"
  - **on_error:** retry
  - **max_retries:** 2

### 3. Select Currencies
- **logic.append**
  - **target:** "${config.currencies}"
  - **item:** "USD"
  - **item_var:** `currency`
  - **extend:** "currency"

### 4. Select Start and End Dates
- **logic.append**
  - **target:** "${config.month.date}"
  - **item:** "2023-10-01"
  - **item_var:** `start_date`
  - **extend:** "start_date"

### 5. Open Date Picker
- **web.select_option**
  - **selector:** ".react-datepicker select:nth-child(1)"
  - **value:** "2023-10-01"
  - **on_error:** retry
  - **max_retries:** 2

### 6. Select Month and Day
- **logic.append**
  - **target:** "${config.month.date}"
  - **item:** "2023-10-01"
  - **item_var:** `start_date`
  - **extend:** "start_date"

### 7. Open End Date Picker
- **logic.append**
  - **target:** "${config.month.date}"
  - **item:** "2023-10-31"
  - **item_var:** `end_date`
  - **extend:** "end_date"

### 8. Click Search
- **web.click**
  - **selector:** ".historical-btn"

### 9. Write to CSV
- **csv.write**
  - **file_path:** "${output_path}"
  - **data:** "${currencies}"
  - **on_error:** retry
  - **max_retries:** 2

### 10. Close Browser and Email
- **web.close**
  - **on_error:** retry
  - **max_retries:** 2

### 11. Email CSV
- **email.send**
  - **to:** "${config_email.to}"
  - **cc:** ""
  - **bcc:** ""
  - **subject:** "${config_email_subject}"
  - **body:** "${config_email_body}"
  - **html:** ""
  - **attachments:** ""
  - **smtp_host:** "smtp.example.com"
  - **smtp_port:** 587
  - **smtp_user:** "user@example.com"
  - **smtp_password:** "password"
  - **use_tls:** true
  - **dry_run:** "${config_email_dry_run}"

### 12. Retry on Error
- **logic.append**
  - **target:** "${output_path}"
  - **item:** "1"
  - **extend:** "retry_count"

### 13. Increment Retry Count
- **logic.set_variable**
  - **name:** "retry_count"
  - **value:** "1"

### 14. Continue Flow
- **flow.return**
  - **value:** "Flow completed successfully."
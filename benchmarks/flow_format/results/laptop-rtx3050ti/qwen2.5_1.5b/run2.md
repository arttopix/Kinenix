# Collect Bank of Thailand Buying Transfer Rates (flow.md)

## Variables
- `config.url`: "https://example.com"
- `config.currencies`: ["THB", "USD", "JPY", "EUR", "AUD"]
- `config.month`: {"date": "today", "add_months": -1}
- `config.output_path`: "/path/to/output"
- `config.email.to`: "email@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config.email.body`: "Please find attached the Bank of Thailand Buying Transfer Rates report."
- `config.email.dry_run`: false

## Steps

### 1. Set Initial Variables
- **config.month.date:** "2023-04-01"
- **config.output_path:** "/path/to/output/bank-of-thailand-report-2023-04-01.csv"

### 2. Open the Website
- **http.request**
    - `url`: `${config.url}`
    - `method`: "GET"
    - `headers`: {}
    - `payload`: {}
    - `timeout`: 10

### 3. Select Currency Filter
- **web.click**
    - `selector`: "#dropdownCurrency > .currency-filter input"
    - `label`: "Select Currency"
    - `timeout`: 5

### 4. Set Start and End Dates
- **web.select_option**
    - `selector`: "#react-datepicker__year-select"
    - `value`: "${config.month.date}年上半年"
    - `timeout`: 5
- **web.select_option**
    - `selector`: "#react-datepicker__month-select"
    - `value`: "6"
    - `timeout`: 5
- **web.select_option**
    - `selector`: "#react-datepicker__day-select"
    - `value`: "30"
    - `timeout`: 5

### 5. Search for Historical Rates
- **web.click**
    - `selector`: ".historical-btn"
    - `label`: "Search"
    - `timeout`: 5

### 6. Collect Data for Each Currency
- **logic.loop**
    - **items:** `${config.currencies}`
    - **item_var:** `currency`
    - **Sub-steps:**
      - **web.select_option**
          - `selector`: "#react-datepicker__year-select"
          - `value`: "${config.month.date}年上半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__month-select"
          - `value`: "${config.month.date}年上半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__day-select"
          - `value`: "${config.currencies[currency]}"
          - `timeout`: 5
      - **web.click**
          - `selector`: ".historical-btn"
          - `label`: "Search"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__year-select"
          - `value`: "${config.month.date}年下半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__month-select"
          - `value`: "${config.month.date}年下半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__day-select"
          - `value`: "${config.currencies[currency]}"
          - `timeout`: 5
      - **web.click**
          - `selector`: ".historical-btn"
          - `label`: "Search"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__year-select"
          - `value`: "${config.month.date}上半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__month-select"
          - `value`: "${config.month.date}上半年"
          - `timeout`: 5
      - **web.select_option**
          - `selector`: "#react-datepicker__day-select"
          - `value`: "${config.currencies[currency]}"
          - `timeout`: 5
      - **web.click**
          - `selector`: ".historical-btn"
          - `label`: "Search"
          - `timeout`: 5

### 7. Write Data to CSV
- **csv.write**
    - `file_path`: "/path/to/output/bank-of-thailand-report-2023-04-01.csv"
    - `data`: `${rows}`
    - `on_error`: retry
    - `max_retries`: 2

### 8. Close Browser and Email Report
- **http.download**
    - `url`: "https://example.com"
    - `target_path`: "/path/to/report/report.html"
    - `timeout`: 10
- **logic.delay**
    - `seconds`: 10
- **email.send**
    - `to`: "${config.email.to}"
    - `cc`: ""
    - `bcc`: ""
    - `subject`: "${config.email.subject}"
    - `body`: "${config.email.body}"
    - `html`: false
    - `attachments`: []
    - `smtp_host`: ""
    - `smtp_port`: ""
    - `smtp_user`: ""
    - `smtp_password`: ""
    - `use_tls`: false
    - `dry_run`: false

### 9. Retry in Case of Error
- **logic.retry**
    - `message`: "The report could not be collected."
    - `category`: "error"

### 10. Cleanup
- **file.delete**
    - `path`: "/path/to/output/bank-of-thailand-report-2023-04-01.csv"
    - `missing_ok`: true

This flow automates the process of collecting Bank of Thailand buying transfer rates for specified currencies over a month, converting them into a CSV file that can be sent via email.
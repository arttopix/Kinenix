# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config.month.date`: "2023-04-01"
- `config.currencies`: ["THB", "EUR", "JPY", "INR"]
- `config.url`: "https://www.bangkokbank.com/transaction-history"
- `config.output_path`: "/tmp/bank_of_thailand_transfer_rates.csv"
- `config.email.to`: "recipient@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config.email.body`: "Please find the report attached."
- `config.email.dry_run`: false

## Steps

### 1. Determine the Month and First/Last Date (`logic.set_variable`)
- **name:** `config.month`
- **value:** "today add_months -1"

### 2. Open the URL with Cookie Acceptance (`http.request`)
- **url:** `${config.url}`
- **method:** "GET"
- **headers:** {"Accept": "*/*"}
- **payload:** {}
- **timeout:** 10
- **output_var:** `config.response`

### 3. Filter the Currencies (`logic.set_variable`)
- **name:** `config.currencies`
- **value:** `${config.currencies}`

### 4. Select the Date Range (`logic.set_variable`)
- **name:** `config.month.date`
- **value:** "2023-04-01"

### 5. Open the Currency Filter (`web.open`)
- **url:** `${config.url}`
- **headless:** true
- **timeout:** 10

### 6. Click on the Start and End Dates (`logic.set_variable`)
- **name:** `config.month.date`
- **value:** "2023-04-01"

### 7. Click on the Search Button (`web.click`)
- **selector:** ".historical-btn"
- **label:** "Search"
- **timeout:** 5

### 8. Select Each Currency (`logic.set_variable`)
- **name:** `config.currencies`
- **value:** "${config.currencies}"
- **output_var:** `config.selectors`
- **sub-steps:**
  - 8.1. Select the Currency (`web.select_option`)
    - **selector:** "input[name='currencyCheck'][value='THB']"
    - **label:** "THB"
    - **value:** "THB"
    - **timeout:** 10
  - 8.2. Select the Currency (`web.select_option`)
    - **selector:** "input[name='currencyCheck'][value='EUR']"
    - **label:** "EUR"
    - **value:** "EUR"
    - **timeout:** 10
  - 8.3. Select the Currency (`web.select_option`)
    - **selector:** "input[name='currencyCheck'][value='JPY']"
    - **label:** "JPY"
    - **value:** "JPY"
    - **timeout:** 10
  - 8.4. Select the Currency (`web.select_option`)
    - **selector:** "input[name='currencyCheck'][value='INR']"
    - **label:** "INR"
    - **value:** "INR"
    - **timeout:** 10

### 9. Read the Table and Write to CSV (`logic.set_variable`)
- **name:** `config.output_path`
- **value:** "${config.output_path}"
- **data:** "${config.selectors}"
- **on_error:** retry
- **max_retries:** 2
- **sub-steps:**
  - 9.1. Write to CSV (`csv.write`)
    - **file_path:** "${config.output_path}"
    - **data:** "${config.selectors}"
    - **columns:** "Currency, Date, Buying Transfer Rate"
    - **append:** false
    - **encoding:** "utf-8"
    - **output_var:** `config.result`

### 10. Close the Browser and Send Email (`logic.set_variable`)
- **name:** `config.email.to`
- **value:** "${config.email.to}"
- **output_var:** `config.result`
- **sub-steps:**
  - 10.1. Close the Browser (`web.close`)
  - 10.2. Send Email (`email.send`)
    - **to:** "${config.email.to}"
    - **cc:** ""
    - **bcc:** ""
    - **subject:** "${config.email.subject}"
    - **body:** "${config.email.body}"
    - **html:** false
    - **attachments:** []
    - **smtp_host:** ""
    - **smtp_port:** 25
    - **smtp_user:** ""
    - **smtp_password:** ""
    - **use_tls:** false
    - **dry_run:** "${config.email.dry_run}"

### 11. Handle Errors (`logic.set_variable`)
- **name:** `config.result`
- **value:** `false`
- **output_var:** `config.result`
- **sub-steps:**
  - 11.1. Retry (2 attempts)
    - **message:** "Failed to collect or write CSV. Retrying..."
    - **category:** "error"

### 12. Report Progress and Finalize (`logic.set_variable`)
- **name:** `config.result`
- **value:** `true`
- **output_var:** `config.result`
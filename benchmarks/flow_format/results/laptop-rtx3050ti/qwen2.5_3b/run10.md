# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config.month.date`: today
- `config.month.add_months`: -1
- `config.url`: "https://www.kinenix.com"
- `config.currencies`: ["THB", "USD", "EUR", "JPY"]
- `config.output_path`: "./output/bank_of_thailand.csv"
- `config.email.to`: "recipient@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config.email.body`: "Please find attached the Bank of Thailand buying transfer rates report for the specified period."
- `config.headless`: "True"
- `config.email.dry_run`: "False"

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "now"
- **input_format:** "%Y-%m-%d"
- **add_months:** -1
- **add_days:** 1
- **output_var:** `config.month`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **Work out the first day of the month (`date.calc`):**
    - **date:** "${config.month.date}"
    - **input_format:** "%Y-%m-%d"
    - **add_days:** 1
    - **output_var:** `config.first_day`
  - **Work out the last day of the month (`date.calc`):**
    - **date:** "${config.first_day.date}"
    - **input_format:** "%Y-%m-%d"
    - **add_days:** 1
    - **output_var:** `config.last_day`
  - **Open the first day of the month (`web.open`):**
    - **url:** "${config.first_day}"
    - **headless:** "${config.headless}"
    - **timeout:** 10
  - **Click the Accept recommended cookies button (`web.click`):**
    - **selector:** ".react-cookie-banner > button:contains('Accept recommended cookies')"
    - **timeout:** 5

### 2. Open the currency filter and tick each currency (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "Open the dropdown"
- **item:** "${item}"
- **action:** "web.select_option"
- **value:** ".currency-filter input[name='currencyCheck'][value='THB']"
- **index:** 0
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - **Check the currency checkbox (`web.select_option`):**
    - **value:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **timeout:** 3

### 3. Pick the start and end dates in the date picker (`web.click`)
- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **value:** "${config.month.date}"
- **item_var:** `month`
- **Sub-steps:**
  - **Click the month selection (`web.click`):**
    - **selector:** ".react-datepicker select >> nth=0"
    - **timeout:** 5
  - **Click the day selection (`web.click`):**
    - **selector:** ".react-datepicker select >> nth=1"
    - **label:** "${config.first_day.date}"
    - **value:** "${config.first_day.date}"
    - **timeout:** 5
- **Click the month selection (`web.click`):**
  - **selector:** ".react-datepicker select >> nth=0"
  - **label:** "Month"
  - **value:** "${config.month.date}"
  - **item_var:** `month`
  - **Sub-steps:**
    - **Click the day selection (`web.click`):**
      - **selector:** ".react-datepicker select >> nth=1"
      - **label:** "${config.last_day.date}"
      - **value:** "${config.last_day.date}"
      - **timeout:** 5

### 4. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **action:** "web.click"
- **timeout:** 5

### 5. For each currency, click its tab button and read the visible table (`web.click` and `web.get_table`)
- **selector:** "button:contains('${currency}')"
- **label:** "Click tab button"
- **action:** "web.click"
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - **Get the table (`web.get_table`):**
    - **selector:** ".table > tbody"
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **numeric_columns:** ["Buying Rates Transfer"]
    - **add_columns:** ["Currency"]
    - **min_rows:** 1
    - **timeout:** 5
  - **Write the table rows to CSV (`csv.write`):**
    - **file_path:** "${config.output_path}"
    - **data:** `${table}`
    - **columns:** ["Currency", "Date", "Buying Transfer Rate"]
    - **encoding:** "utf-8"
    - **append:** "False"
    - **output_var:** `table`
    - **on_error:** retry
    - **max_retries:** 2

### 6. Close the browser and email the CSV (`web.close` and `email.send`)
- **Close the browser (`web.close`):**
- **Write the CSV file (`csv.write`):**
  - **file_path:** "${config.output_path}"
  - **data:** `${table}`
  - **columns:** ["Currency", "Date", "Buying Transfer Rate"]
  - **encoding:** "utf-8"
  - **append:** "False"
  - **output_var:** `table`
  - **on_error:** retry
  - **max_retries:** 2
- **Email the CSV (`email.send`):**
  - **to:** "${config.email.to}"
  - **subject:** "${config.email.subject}"
  - **body:** "${config.email.body}"
  - **html:** "False"
  - **attachments:** "${config.output_path}"
  - **smtp_host:** "smtp.example.com"
  - **smtp_port:** 587
  - **smtp_user:** "user@example.com"
  - **smtp_password:** "password"
  - **use_tls:** "True"
  - **dry_run:** "${config.email.dry_run}"
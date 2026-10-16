# Collect Bank of Thailand Transfer Rates

## Variables
- `base_url`: "https://www.bangkokbank.com"
- `config.month`: {"date": "today", "add_months": -1}
- `config.currencies`: ["THB", "USD", "EUR", "JPY", "GBP"]
- `config.output_path`: "./output/bank_of_thailand_transfer_rates.csv"
- `config.email.to`: "recipient@example.com"
- `config.email.subject`: "Bank of Thailand Transfer Rates Report"
- `config.email.body`: "Please find the attached CSV file with the Bank of Thailand transfer rates."
- `config.email.dry_run`: false
- `config.headless`: true
- `config.url`: "https://www.bangkokbank.com"

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** "${config.month.add_months}"
- **output_var:** `month_range`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Open Browser (`web.open`)
    - **url:** "${base_url}"
    - **headless:** ${config.headless}
    - **output_var:** `browser`

### 2. Open the currency filter and tick each currency (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **label:** "${config.currencies.join(', ')}"
- **value:** "${config.currencies}"
- **text:** "${config.currencies.join(', ')}"
- **output_var:** `currency_filter`

### 3. Pick the start and end dates in the date picker (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "${month_range.first}"
- **value:** "${month_range.first}"
- **text:** "${month_range.first}"
- **output_var:** `date_picker_start`

- **selector:** ".react-datepicker select >> nth=0"
- **label:** "${month_range.second}"
- **value:** "${month_range.second}"
- **text:** "${month_range.second}"
- **output_var:** `date_picker_end`

### 4. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "#historical-btn"
- **label:** "Search"
- **output_var:** `search_button`

### 5. For each currency, click its tab button and read the visible table (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Open Browser (`web.open`)
    - **url:** "${base_url}"
    - **headless:** ${config.headless}
    - **output_var:** `browser`

  - Pick the start and end dates in the date picker (`web.select_option`)
    - **selector:** ".react-datepicker select >> nth=1"
    - **label:** "${month_range.first}"
    - **value:** "${month_range.first}"
    - **text:** "${month_range.first}"
    - **output_var:** `date_picker_start`

    - **selector:** ".react-datepicker select >> nth=0"
    - **label:** "${month_range.second}"
    - **value:** "${month_range.second}"
    - **text:** "${month_range.second}"
    - **output_var:** `date_picker_end`

  - Click 'button.historical-btn' to search (`web.click`)
    - **selector:** "#historical-btn"
    - **label:** "Search"
    - **output_var:** `search_button`

  - Click the currency tab button (`web.click`)
    - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **label:** "${currency}"
    - **output_var:** `currency_tab`

  - Read the visible table (`web.get_table`)
    - **selector:** ".table-body"
    - **label:** "table-body"
    - **columns:** ["Period", "${currency}"]
    - **numeric_columns:** ["Period"]
    - **add_columns:** ["Currency"]
    - **min_rows:** 0
    - **output_var:** `table`

### 6. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${table}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** false
- **output_var:** `csv_content`

### 7. Close the browser and email the CSV to ${config.email.to} (`email.send`)
- **to:** "${config.email.to}"
- **cc:** "${config.email.cc}"
- **bcc:** "${config.email.bcc}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** false
- **attachments:** "${config.output_path}"
- **smtp_host:** "${config.smtp_host}"
- **smtp_port:** "${config.smtp_port}"
- **smtp_user:** "${config.smtp_user}"
- **smtp_password:** "${config.smtp_password}"
- **use_tls:** "${config.smtp_use_tls}"
- **dry_run:** ${config.email_dry_run}
- **output_var:** `email_status`

### 8. Retry opening the page and searching twice (`logic.loop`)
- **items:** [0, 1]
- **item_var:** `retry`
- **Sub-steps:**
  - Open Browser (`web.open`)
    - **url:** "${base_url}"
    - **headless:** ${config.headless}
    - **output_var:** `browser`

  - Pick the start and end dates in the date picker (`web.select_option`)
    - **selector:** ".react-datepicker select >> nth=1"
    - **label:** "${month_range.first}"
    - **value:** "${month_range.first}"
    - **text:** "${month_range.first}"
    - **output_var:** `date_picker_start`

    - **selector:** ".react-datepicker select >> nth=0"
    - **label:** "${month_range.second}"
    - **value:** "${month_range.second}"
    - **text:** "${month_range.second}"
    - **output_var:** `date_picker_end`

  - Click 'button.historical-btn' to search (`web.click`)
    - **selector:** "#historical-btn"
    - **label:** "Search"
    - **output_var:** `search_button`

### 9. Retry writing the CSV twice (`logic.loop`)
- **items:** [0, 1]
- **item_var:** `retry`
- **Sub-steps:**
  - Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
    - **file_path:** "${config.output_path}"
    - **data:** `${csv_content}`
    - **columns:** ["Currency", "Date", "Buying Transfer Rate"]
    - **encoding:** "utf-8"
    - **append:** false
    - **output_var:** `csv_content`

### 10. Retry screenshot twice (`logic.loop`)
- **items:** [0, 1]
- **item_var:** `retry`
- **Sub-steps:**
  - Screenshot (`web.screenshot`)
    - **path:** "${config.output_path}/screenshot.png"
    - **full_page:** true
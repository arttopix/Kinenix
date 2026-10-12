# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `report_start_date`: ${config.month.date}
- `report_end_date`: ${date.calc(date: report_start_date, add_months: 0, format: "yyyy-MM-dd")}
- `currencies`: ${config.currencies}
- `output_path`: ${config.output_path}
- `headless`: ${config.headless}
- `email.to`: ${config.email.to}
- `email.subject`: ${config.email.subject}
- `email.body`: ${config.email.body}
- `email.dry_run`: ${config.email.dry_run}

## Steps

### 1. Open Bank of Thailand Page (`web.open`)
- **url:** ${config.url}
- **description:** Open Bank of Thailand page to accept cookie banner
- **output_var:** `page`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Accept Cookies (`web.click`):
    - **selector:** button.historical-btn

### 2. Open Currency Filter (`web.click`)
- **selector:** #dropdownCurrency
- **description:** Click on the currency filter dropdown
- **output_var:** `currency_filter`
- **on_error:** retry
- **max_retries:** 2

### 3. Tick Each Currency (`logic.loop`)
- **items:** `${currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`web.click`):
    - **selector:** .currency-filter input[name='currencyCheck'][value='${currency}']

### 4. Set Start and End Dates (`web.select_option`)
- **selector:** .react-datepicker select >> nth=1
- **description:** Set year in date picker
- **output_var:** `year_select`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Set Month (`web.select_option`):
    - **selector:** .react-datepicker select >> nth=0
    - **value:** ${report_start_date.month}
    - **description:** Set month in date picker
    - **output_var:** `month_select`
    - **on_error:** retry
    - **max_retries:** 2
    - **Sub-steps:**
      - Set Start Date (`web.click`):
        - **selector:** .react-datepicker table tbody tr td.text-center
        - **value:** ${report_start_date.day}
        - **description:** Set start date in date picker
        - **output_var:** `start_date`
        - **on_error:** retry
        - **max_retries:** 2
- **selector:** .react-datepicker select >> nth=1
- **description:** Set year in date picker
- **output_var:** `year_select`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Set Month (`web.select_option`):
    - **selector:** .react-datepicker select >> nth=0
    - **value:** ${report_end_date.month}
    - **description:** Set month in date picker
    - **output_var:** `month_select`
    - **on_error:** retry
    - **max_retries:** 2
    - **Sub-steps:**
      - Set End Date (`web.click`):
        - **selector:** .react-datepicker table tbody tr td.text-center
        - **value:** ${report_end_date.day}
        - **description:** Set end date in date picker
        - **output_var:** `end_date`
        - **on_error:** retry
        - **max_retries:** 2

### 5. Search Historical Rates (`web.click`)
- **selector:** button.historical-btn
- **description:** Search for historical rates
- **output_var:** `search_result`
- **on_error:** retry
- **max_retries:** 2

### 6. Iterate Over Currencies (`logic.loop`)
- **items:** `${currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Switch to Currency Tab (`web.click`):
    - **selector:** ${currency}
    - **description:** Switch to currency tab
    - **output_var:** `currency_tab`
    - **on_error:** retry
    - **max_retries:** 2
  - Read Table (`web.get_table`):
    - **selector:** .table > tbody
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **numeric_columns:** ["Buying Rates Transfer"]
    - **description:** Read the table
    - **output_var:** `table_data`
    - **on_error:** retry
    - **max_retries:** 2

### 7. Append Currency Column (`logic.append`):
- **target:** `table_data`
- **item:** {"Currency": "${currency}"}
- **description:** Append currency column to table data
- **output_var:** `table_data_with_currency`
- **on_error:** retry
- **max_retries:** 2

### 8. Write CSV (`csv.write`)
- **file_path:** ${output_path}
- **data:** `${table_data_with_currency}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **description:** Write CSV file
- **output_var:** `csv_file`
- **on_error:** retry
- **max_retries:** 2

### 9. Close Browser (`web.close`)

### 10. Email CSV (`email.send`)
- **to:** ${email.to}
- **subject:** ${email.subject}
- **body:** ${email.body}
- **html:** `<a href="${output_path}">${output_path}</a>`
- **description:** Email CSV file
- **output_var:** `email_status`
- **on_error:** retry
- **max_retries:** 2
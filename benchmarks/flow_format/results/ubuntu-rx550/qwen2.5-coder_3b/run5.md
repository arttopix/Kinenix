# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `start_date`: ${date.calc(date: ${config.month.date}, input_format: "YYYY-MM-DD", add_months: -1)}
- `end_date`: ${date.calc(date: ${config.month.date}, input_format: "YYYY-MM-DD", add_months: -1, add_days: -1)}
- `currency_data`: []
- `report_data`: []
- `output_path`: ${config.output_path}

## Steps

### 1. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **description:** Open the Bank of Thailand website
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Accept Cookies (`web.click`):
    - **selector:** button.historical-btn
    - **description:** Accept cookies

### 2. Select Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`):
    - **selector:** .currency-filter input[name='currencyCheck'][value='${currency}']
    - **description:** Click currency tab
    - **on_error:** retry
    - **max_retries:** 2
  - Get Table Data (`web.get_table`):
    - **selector:** .table-data
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **description:** Get table data
    - **on_error:** retry
    - **max_retries:** 2

### 3. Extract and Format Data (`logic.loop`)
- **items:** ${currency_data}
- **item_var:** `data`
- **Sub-steps:**
  - Add Currency Column (`logic.append`):
    - **target:** report_data
    - **item:** {"Currency": "${currency}", "Date": "${data[0]}", "Buying Transfer Rate": "${data[1]}"}

### 4. Write to CSV (`csv.write`)
- **file_path:** ${output_path}
- **data:** `${report_data}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **description:** Write to CSV
- **on_error:** retry
- **max_retries:** 2

### 5. Close Browser (`web.close`)
- **description:** Close the browser

### 6. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** [${output_path}]
- **description:** Send email
- **on_error:** retry
- **max_retries:** 2

## Notes
- Replace `${config.month.date}`, `${config.month.add_months}`, `${config.output_path}`, `${config.headless}`, `${config.email.to}`, `${config.email.subject}`, `${config.email.body}`, and `${config.email.dry_run}` with actual values.
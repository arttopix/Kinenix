# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: {}
- `report_start`: {}
- `report_end`: {}
- `currencies`: {}
- `output_path`: {}
- `csv_data`: {}
- `email_data`: {}

## Steps

### 1. Set Report Start and End Dates (`date.calc`)
- **date:** today
- **input_format:** "YYYY-MM-DD"
- **add_months:** -1
- **output_var:** `report_start`
- **description:** "Calculate the first day of the previous month."
- **max_retries:** 2
- **retry_interval:** 5

### 2. Set Report End Dates (`date.calc`)
- **date:** today
- **input_format:** "YYYY-MM-DD"
- **add_months:** -1
- **add_days:** -1
- **output_var:** `report_end`
- **description:** "Calculate the last day of the previous month."
- **max_retries:** 2
- **retry_interval:** 5

### 3. Initialize CSV Data (`logic.set_variable`)
- **name:** `csv_data`
- **value:** {}

### 4. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **description:** "Open the Bank of Thailand website."
- **output_var:** `browser`
- **max_retries:** 2
- **retry_interval:** 5

### 5. Accept Cookie Banner (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Accept recommended cookies"
- **description:** "Accept the cookie banner if it appears."
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 6. Select Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Select Currency (`web.select_option`):
    - **selector:** "#dropdownCurrency"
    - **value:** "${currency}"
    - **description:** "Select the currency."
    - **max_retries:** 2
    - **retry_interval:** 5

### 7. Set Start Date (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **value:** "${report_start.year}"
- **description:** "Set the start year."
- **max_retries:** 2
- **retry_interval:** 5

### 8. Set Start Month (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${report_start.month}"
- **description:** "Set the start month."
- **max_retries:** 2
- **retry_interval:** 5

### 9. Set Start Day (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1" (day cell text)
- **value:** "${report_start.day}"
- **description:** "Set the start day."
- **max_retries:** 2
- **retry_interval:** 5

### 10. Set End Date (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1" (day cell text)
- **value:** "${report_end.day}"
- **description:** "Set the end day."
- **max_retries:** 2
- **retry_interval:** 5

### 11. Set End Month (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${report_end.month}"
- **description:** "Set the end month."
- **max_retries:** 2
- **retry_interval:** 5

### 12. Set End Year (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **value:** "${report_end.year}"
- **description:** "Set the end year."
- **max_retries:** 2
- **retry_interval:** 5

### 13. Search for Historical Rates (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **description:** "Search for historical rates."
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 14. Get Currency Tabs (`web.get_table`)
- **selector:** "div.tab-content"
- **item_var:** `currency_tab`
- **description:** "Get the currency tabs."
- **output_var:** `currency_tabs`
- **max_retries:** 2
- **retry_interval:** 5

### 15. Loop Through Currency Tabs (`logic.loop`)
- **items:** `${currency_tabs}`
- **item_var:** `currency_tab`
- **Sub-steps:**
  - Click Currency Tab (`web.click`):
    - **selector:** `div.tab-content div.tab-item a:contains("${currency_tab}")`
    - **label:** "Click currency tab"
    - **description:** "Click the currency tab."
    - **max_retries:** 2
    - **retry_interval:** 5

### 16. Get Table Data (`web.get_table`)
- **selector:** "table.table"
- **item_var:** `data_row`
- **description:** "Get the table data."
- **output_var:** `data_rows`
- **max_retries:** 2
- **retry_interval:** 5

### 17. Format Table Data (`logic.append`)
- **target:** `csv_data`
- **item:** {"Currency": "${currency}", "Date": "${data_row['Period']}", "Buying Transfer Rate": "${data_row['Buying Rates Transfer']}"}
- **description:** "Format the table data."
- **max_retries:** 2
- **retry_interval:** 5

### 18. Close Browser (`web.close`)
- **description:** "Close the browser."
- **max_retries:** 2
- **retry_interval:** 5

### 19. Prepare Email Data (`logic.set_variable`)
- **name:** `email_data`
- **value:** {"to": ${config.email.to}, "subject": "${config.email.subject}", "body": "Please find the attached CSV file.", "html": "<p>Please find the attached CSV file.</p>", "attachments": ["${output_path}"]}
- **description:** "Prepare the email data."
- **max_retries:** 2
- **retry_interval:** 5

### 20. Send Email (`email.send`)
- **to:** ${config.email.to}
- **cc:** ${config.email.cc}
- **bcc:** ${config.email.bcc}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **html:** ${config.email.html}
- **attachments:** ${config.email.attachments}
- **smtp_host:** ${config.email.smtp_host}
- **smtp_port:** ${config.email.smtp_port}
- **smtp_user:** ${config.email.smtp_user}
- **smtp_password:** ${config.email.smtp_password}
- **use_tls:** ${config.email.use_tls}
- **dry_run:** ${config.email.dry_run}
- **description:** "Send the email."
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 21. Append CSV Data to Output File (`csv.write`)
- **file_path:** ${output_path}
- **data:** ${csv_data}
- **description:** "Append the CSV data to the output file."
- **max_retries:** 2
- **retry_interval:** 5
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `first_day`: (empty)
- `last_day`: (empty)
- `currency_filter_values`: (empty)
- `currency_table`: (empty)
- `output_data`: (empty)

## Steps

### 1. Calculate Report Date (`date.calc`)
- **date:** ${config.month.date}
- **input_format:** "%Y-%m-%d"
- **add_months:** -1
- **output_var:** `first_day`
- **description:** Calculate the first day of the report month.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 2. Calculate Last Day of Report Month (`date.calc`)
- **date:** ${config.month.date}
- **input_format:** "%Y-%m-%d"
- **add_months:** -1
- **add_days:** -1
- **output_var:** `last_day`
- **description:** Calculate the last day of the report month.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 3. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **output_var:** `browser`
- **description:** Open the Bank of Thailand website.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 4. Accept Cookie Banner (`web.click`)
- **selector:** '.accept-button'
- **label:** 'Accept recommended cookies'
- **output_var:** `cookie_accepted`
- **description:** Accept the cookie banner if it appears.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 5. Select Currency Filter (`web.click`)
- **selector:** '#dropdownCurrency'
- **label:** 'Currency filter'
- **output_var:** `currency_filter_selected`
- **description:** Select the currency filter.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 6. Set Currency Filter Values (`logic.append`)
- **target:** `currency_filter_values`
- **item:** "${currency}" for each ${config.currencies}
- **output_var:** `currency_filter_values`
- **description:** Set the currency filter values.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 7. Select Each Currency (`logic.loop`)
- **items:** `currency_filter_values`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency (`web.click`):
    - **selector:** `.currency-filter input[name='currencyCheck'][value='${currency}']`
    - **label:** ${currency}
    - **output_var:** `currency_selected`
    - **description:** Select the currency.
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5

### 8. Set Start Date (`web.get_attribute`)
- **selector:** '.react-datepicker select >> nth=1'
- **label:** 'Year'
- **attribute:** 'value'
- **name:** `start_year`
- **output_var:** `start_year`
- **description:** Set the start year.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 9. Set End Date (`web.get_attribute`)
- **selector:** '.react-datepicker select >> nth=0'
- **label:** 'Month'
- **attribute:** 'value'
- **name:** `start_month`
- **output_var:** `start_month`
- **description:** Set the start month.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 10. Set Day (`web.click`)
- **selector:** '.react-datepicker select >> nth=0 >> option[value="${start_month}"]'
- **label:** 'Month'
- **output_var:** `month_selected`
- **description:** Set the month.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 11. Set Start Date Day (`web.click`)
- **selector:** '.react-datepicker select >> nth=0 >> option[value="${start_month}"] >> .. >> option[value="${first_day}"]'
- **label:** 'Day'
- **output_var:** `day_selected`
- **description:** Set the start date day.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 12. Set End Date Day (`web.click`)
- **selector:** '.react-datepicker select >> nth=0 >> option[value="${last_day}"] >> .. >> option[value="${last_day}"]'
- **label:** 'Day'
- **output_var:** `end_day_selected`
- **description:** Set the end date day.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 13. Click Search Button (`web.click`)
- **selector:** 'button.historical-btn'
- **label:** 'Search'
- **output_var:** `search_clicked`
- **description:** Click the search button.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 14. Get Currency Tab Rows (`web.get_table`)
- **selector:** 'table > tbody'
- **label:** 'Currency tab'
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **output_var:** `currency_table`
- **description:** Get the currency tab rows.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 15. Set Currency Table Rows (`logic.append`)
- **target:** `output_data`
- **item:** {"Currency": currency, ...row} for each `row` in `currency_table`
- **output_var:** `output_data`
- **description:** Set the currency table rows.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 16. Write CSV File (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** `${output_data}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **output_var:** `csv_written`
- **description:** Write the CSV file.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 17. Close Browser (`web.close`)
- **output_var:** `browser_closed`
- **description:** Close the browser.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 18. Email CSV (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **html:** (empty)
- **attachments:** ${config.output_path}
- **smtp_host:** (empty)
- **smtp_port:** (empty)
- **smtp_user:** (empty)
- **smtp_password:** (empty)
- **use_tls:** (empty)
- **dry_run:** ${config.email.dry_run}
- **output_var:** `email_sent`
- **description:** Email the CSV.
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 19. End (`flow.return`)
- **value:** `email_sent`
- **description:** End the flow.
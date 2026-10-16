# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: <initial value>
- `rows`: []
- `csv_data`: []
- `csv_output_path`: <initial value>
- `error_count`: 0
- `max_retries`: 2
- `retry_interval`: 5

## Steps

### 1. Calculate Start and End Dates (`date.calc`)
- **date:** today
- **input_format:** "%Y-%m-%d"
- **add_months:** -1
- **output_var:** `first_day`
- **description:** Calculate the first day of the previous month.
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Calculate Last Day (`date.calc`):
    - **date:** first_day
    - **add_days:** 30
    - **output_var:** `last_day`
    - **description:** Calculate the last day of the previous month.

### 2. Open Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **output_var:** `page`
- **description:** Open the Bank of Thailand website.
- **on_error:** retry
- **max_retries:** 2

### 3. Accept Cookie Banner (`web.click`)
- **selector:** '.accept-recommended-cookies'
- **label:** Cookie banner
- **description:** Accept the cookie banner if it appears.
- **output_var:** `cookie_banner_accepted`
- **on_error:** retry
- **max_retries:** 2

### 4. Open Currency Filter (`web.click`)
- **selector:** '#dropdownCurrency'
- **label:** Currency filter
- **description:** Open the currency filter dropdown.
- **output_var:** `currency_filter_opened`
- **on_error:** retry
- **max_retries:** 2

### 5. Tick Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`web.click`):
    - **selector:** `.currency-filter input[name='currencyCheck'][value='${currency}']`
    - **label:** Currency check
    - **description:** Check the currency in the filter.
    - **output_var:** `currency_checked`
    - **on_error:** retry
    - **max_retries:** 2

### 6. Select Date Range (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=1'
- **label:** Year
- **value:** 2023
- **description:** Select the year.
- **output_var:** `year_selected`
- **on_error:** retry
- **max_retries:** 2

### 7. Select Start Date (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=0'
- **label:** Month
- **value:** ${first_day.month}
- **description:** Select the month.
- **output_var:** `month_selected`
- **on_error:** retry
- **max_retries:** 2

### 8. Select Start Date (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=0'
- **label:** Day
- **value:** ${first_day.day}
- **description:** Select the day.
- **output_var:** `start_date_selected`
- **on_error:** retry
- **max_retries:** 2

### 9. Select End Date (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=1'
- **label:** Year
- **value:** 2023
- **description:** Select the year.
- **output_var:** `year_selected`
- **on_error:** retry
- **max_retries:** 2

### 10. Select End Date (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=0'
- **label:** Month
- **value:** ${last_day.month}
- **description:** Select the month.
- **output_var:** `month_selected`
- **on_error:** retry
- **max_retries:** 2

### 11. Select End Date (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=0'
- **label:** Day
- **value:** ${last_day.day}
- **description:** Select the day.
- **output_var:** `end_date_selected`
- **on_error:** retry
- **max_retries:** 2

### 12. Search Historical Rates (`web.click`)
- **selector:** 'button.historical-btn'
- **label:** Search button
- **description:** Search for historical rates.
- **output_var:** `search_clicked`
- **on_error:** retry
- **max_retries:** 2

### 13. Switch to Currency Tab (`web.click`)
- **selector:** 'button:has-text("${currency}")'
- **label:** Currency tab
- **description:** Switch to the currency tab.
- **output_var:** `currency_tab_switched`
- **on_error:** retry
- **max_retries:** 2

### 14. Get Table Data (`web.get_table`)
- **selector:** '.table'
- **label:** Historical rates table
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **description:** Get the historical rates table data.
- **output_var:** `table_data`
- **on_error:** retry
- **max_retries:** 2

### 15. Append Data to CSV (`logic.append`)
- **target:** rows
- **item:** `table_data`
- **description:** Append the table data to the rows list.
- **output_var:** `data_appended`
- **on_error:** retry
- **max_retries:** 2

### 16. Close Browser (`web.close`)
- **description:** Close the browser.
- **on_error:** retry
- **max_retries:** 2

### 17. Write CSV (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **description:** Write the CSV file.
- **output_var:** `csv_written`
- **on_error:** retry
- **max_retries:** 2

### 18. Email CSV (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **html:** true
- **attachments:** ${config.output_path}
- **smtp_host:** <SMTP host>
- **smtp_port:** <SMTP port>
- **smtp_user:** <SMTP user>
- **smtp_password:** <SMTP password>
- **use_tls:** true
- **description:** Email the CSV file.
- **on_error:** retry
- **max_retries:** 2

### 19. Check Error Count (`logic.if`)
- **condition:** ${error_count} > ${max_retries}
- **left:** ${error_count}
- **operator:** gt
- **right:** ${max_retries}
- **Sub-steps:**
  - Log Error (`logic.set_variable`):
    - **name:** error_log
    - **value:** "Error count exceeded ${max_retries}"
    - **description:** Log the error.
- **Else:** (continue)

### 20. Increment Error Count (`logic.set_variable`)
- **name:** error_count
- **value:** ${error_count} + 1
- **description:** Increment the error count.
- **on_error:** retry
- **max_retries:** 2
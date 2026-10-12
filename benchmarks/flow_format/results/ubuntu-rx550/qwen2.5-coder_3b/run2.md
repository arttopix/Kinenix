# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `first_day`: `${date.calc("${config.month.date}", {"format": "YYYY-MM-DD", "add_months": -1})}`
- `last_day`: `${date.calc("${config.month.date}", {"format": "YYYY-MM-DD", "add_months": -1})}`
- `start_date`: `${first_day}`
- `end_date`: `${last_day}`
- `output_path`: `${config.output_path}`
- `email_to`: `${config.email.to}`
- `email_subject`: `${config.email.subject}`
- `email_body`: `${config.email.body}`
- `email_dry_run`: `${config.email.dry_run}`
- `currency_data`: []
- `rows`: []

## Steps

### 1. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **description:** Open the Bank of Thailand website.
- **output_var:** `browser`
- **max_retries:** 2
- **Sub-steps:**
  - Accept Cookie Banner (`ai.prompt`):
    - **system:** "You are on the Bank of Thailand website. Click 'Accept recommended cookies' if it appears."
    - **prompt:** "Click 'Accept recommended cookies'"
    - **timeout:** 10
  - Select Currency Filter (`web.select_option`):
    - **selector:** '#dropdownCurrency'
    - **value:** ${config.currencies}
    - **timeout:** 10

### 2. Set Start and End Dates (`web.get_attribute`)
- **selector:** '.react-datepicker select >> nth=1'
- **attribute:** 'value'
- **output_var:** `year`
- **max_retries:** 2
- **Sub-steps:**
  - Set Year (`web.select_option`):
    - **selector:** '.react-datepicker select >> nth=1'
    - **value:** ${year}
    - **timeout:** 10
  - Set Month (`web.select_option`):
    - **selector:** '.react-datepicker select >> nth=0'
    - **value:** ${config.month.date}
    - **timeout:** 10
  - Set Start Date (`web.select_option`):
    - **selector:** '.react-datepicker select >> nth=0'
    - **value:** ${start_date}
    - **timeout:** 10
  - Set End Date (`web.select_option`):
    - **selector:** '.react-datepicker select >> nth=0'
    - **value:** ${end_date}
    - **timeout:** 10

### 3. Search Historical Rates (`web.click`)
- **selector:** 'button.historical-btn'
- **description:** Search for historical rates.
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Click Search Button (`web.click`):
    - **selector:** 'button.historical-btn'
    - **timeout:** 10

### 4. Collect Currency Data (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Get Currency Tab (`web.click`):
    - **selector:** 'button.historical-btn >> nth=0'
    - **label:** ${currency}
    - **timeout:** 10
    - **wait_for_response:** true
    - **response_timeout:** 10
  - Get Table Data (`web.get_table`):
    - **selector:** 'table tbody tr'
    - **columns:** ['Date', 'Buying Rates Transfer']
    - **numeric_columns:** []
    - **add_columns:** []
    - **min_rows:** 0
    - **timeout:** 10
    - **output_var:** `table_data`
  - Append Currency Data (`logic.append`):
    - **target:** `currency_data`
    - **item:** {currency: ${currency}, data: ${table_data}}
    - **extend:** true
    - **max_retries:** 2

### 5. Write CSV (`csv.write`)
- **file_path:** ${output_path}
- **data:** `${currency_data}`
- **columns:** ['Currency', 'Date', 'Buying Transfer Rate']
- **on_error:** retry
- **max_retries:** 2

### 6. Close Browser (`web.close`)
- **description:** Close the browser.
- **output_var:** `browser`

### 7. Email CSV (`email.send`)
- **to:** ${email_to}
- **subject:** ${email_subject}
- **body:** ${email_body}
- **html:** true
- **attachments:** ${output_path}
- **smtp_host:** ${config.email.smtp_host}
- **smtp_port:** ${config.email.smtp_port}
- **smtp_user:** ${config.email.smtp_user}
- **smtp_password:** ${config.email.smtp_password}
- **use_tls:** true
- **dry_run:** ${email_dry_run}
- **description:** Send the CSV file via email.

### 8. End (`flow.return`)
- **value:** "Completed"
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `first_day`: ""
- `last_day`: ""
- `currency_data`: []

## Steps

### 1. Calculate First and Last Day (`date.calc`)
- **date:** ${config.month.date}
- **input_format:** %Y-%m-%d
- **add_months:** ${config.month.add_months}
- **format:** %Y-%m-%d
- **output_var:** first_day
- **on_error:** retry
- **max_retries:** 2

### 2. Calculate Last Day (`date.calc`)
- **date:** ${first_day}
- **input_format:** %Y-%m-%d
- **add_months:** 1
- **add_days:** -1
- **format:** %Y-%m-%d
- **output_var:** last_day
- **on_error:** retry
- **max_retries:** 2

### 3. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **timeout:** 30
- **on_error:** retry
- **max_retries:** 2

### 4. Accept Cookie Banner (`web.click`)
- **selector:** button:contains('Accept recommended cookies')
- **timeout:** 10
- **on_error:** continue

### 5. Set Currency Filter (`web.select_option`)
- **selector:** #dropdownCurrency
- **value:** ${config.currencies}
- **on_error:** retry
- **max_retries:** 2

### 6. Set Start Date (`web.select_option`)
- **selector:** .react-datepicker select >> nth=1
- **value:** ${first_day.split('-')[0]}
- **on_error:** retry
- **max_retries:** 2

### 7. Set End Date (`web.select_option`)
- **selector:** .react-datepicker select >> nth=0
- **value:** ${last_day.split('-')[1]}
- **on_error:** retry
- **max_retries:** 2

### 8. Search for Data (`web.click`)
- **selector:** button.historical-btn
- **timeout:** 30
- **on_error:** retry
- **max_retries:** 2

### 9. Loop Through Each Currency (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** a:contains('${currency}')
    - **timeout:** 10
    - **on_error:** continue

  - Get Table Data (`web.get_table`)
    - **selector:** table
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **numeric_columns:** ["Buying Rates Transfer"]
    - **add_columns:** [{"name": "Currency", "value": "${currency}"}]
    - **output_var:** currency_data
    - **on_error:** retry
    - **max_retries:** 2

### 10. Write CSV File (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${currency_data}
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 11. Close Browser (`web.close`)
- **on_error:** continue

### 12. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** ${config.output_path}
- **dry_run:** ${config.email.dry_run}
- **on_error:** continue
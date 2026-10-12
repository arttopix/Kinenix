# Bank of Thailand Transfer Rates

## Variables
- `start_date`: null
- `end_date`: null
- `currency_table`: []
- `output_data`: []

## Steps

### 1. Calculate Start and End Dates (`date.calc`)
- **date:** ${config.month.date}
- **input_format:** %Y-%m-%d
- **add_months:** ${config.month.add_months}
- **format:** %Y-%m-%d
- **output_var:** start_date
- **on_error:** retry
- **max_retries:** 2

### 2. Calculate End Dates (`date.calc`)
- **date:** ${start_date}
- **input_format:** %Y-%m-%d
- **add_months:** 1
- **subtract_days:** 1
- **format:** %Y-%m-%d
- **output_var:** end_date
- **on_error:** retry
- **max_retries:** 2

### 3. Open Bank of Thailand Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **timeout:** 60

### 4. Accept Cookie Banner (`web.click`)
- **selector:** button:contains('Accept recommended cookies')
- **label:** Accept recommended cookies
- **timeout:** 10

### 5. Open Currency Filter (`web.click`)
- **selector:** #dropdownCurrency
- **label:** Currency Filter
- **timeout:** 10

### 6. Select Currencies (`web.select_option`)
- **selector:** .currency-filter input[name='currencyCheck']
- **value:** ${config.currencies}
- **ai_match:** true
- **base_url:** ${config.url}
- **timeout:** 20

### 7. Set Date Picker Year (`web.select_option`)
- **selector:** .react-datepicker select >> nth=1
- **value:** ${start_date.split('-')[0]}
- **timeout:** 10

### 8. Set Date Picker Month (`web.select_option`)
- **selector:** .react-datepicker select >> nth=0
- **value:** ${start_date.split('-')[1]}
- **timeout:** 10

### 9. Set Date Picker Day (`web.type`)
- **selector:** .react-datepicker__day--0${start_date.split('-')[2]}
- **text:** ${start_date.split('-')[2]}
- **timeout:** 10

### 10. Set End Date Picker Year (`web.select_option`)
- **selector:** .react-datepicker select >> nth=1
- **value:** ${end_date.split('-')[0]}
- **timeout:** 10

### 11. Set End Date Picker Month (`web.select_option`)
- **selector:** .react-datepicker select >> nth=0
- **value:** ${end_date.split('-')[1]}
- **timeout:** 10

### 12. Set End Date Picker Day (`web.type`)
- **selector:** .react-datepicker__day--0${end_date.split('-')[2]}
- **text:** ${end_date.split('-')[2]}
- **timeout:** 10

### 13. Search for Transfer Rates (`web.click`)
- **selector:** button.historical-btn
- **label:** Search
- **timeout:** 20

### 14. Collect Transfer Rates for Each Currency (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** button:contains('${currency}')
    - **label:** ${currency}
    - **timeout:** 10
  - Extract Currency Table (`web.get_table`)
    - **selector:** table
    - **columns:** "Period", "Buying Rates Transfer"
    - **numeric_columns:** "Buying Rates Transfer"
    - **add_columns:** {"Currency": "${currency}"}
    - **min_rows:** 1
    - **timeout:** 20
    - **output_var:** currency_table
  - Append Currency Table to Output Data (`logic.append`)
    - **target:** output_data
    - **item:** ${currency_table}
    - **extend:** true

### 15. Write Output Data to CSV (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${output_data}
- **columns:** Currency, Date, Buying Transfer Rate
- **encoding:** utf-8
- **append:** false
- **on_error:** retry
- **max_retries:** 2

### 16. Close Browser (`web.close`)

### 17. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** ${config.output_path}
- **dry_run:** ${config.email.dry_run}
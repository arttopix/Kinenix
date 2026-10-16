# Bank of Thailand Transfer Rates

## Variables
- `first_day`: 
- `last_day`: 
- `rows`: []
- `csv_data`: []

## Steps

### 1. Calculate First and Last Day of Report Month (`date.calc`)
- **date:** ${config.month.date}
- **add_months:** ${config.month.add_months}
- **format:** %Y-%m-%d
- **output_var:** first_day
- **on_error:** retry
- **max_retries:** 2

### 2. Calculate Last Day of Report Month (`date.calc`)
- **date:** ${first_day}
- **add_months:** 1
- **add_days:** -1
- **format:** %Y-%m-%d
- **output_var:** last_day
- **on_error:** retry
- **max_retries:** 2

### 3. Open Bank of Thailand Page (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2

### 4. Accept Cookie Banner (`web.click`)
- **selector:** button:contains('Accept recommended cookies')
- **optional:** true
- **timeout:** 10
- **on_error:** continue

### 5. Select Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency
- **Sub-steps:**
  - Select Currency Checkbox (`web.select_option`)
    - **selector:** .currency-filter input[name='currencyCheck'][value='<currency>']
    - **value:** <currency>
    - **timeout:** 10

### 6. Set Start and End Dates (`web.select_option`)
- **selector:** .react-datepicker select >> nth=0
- **value:** ${first_day.split('-')[1]}  # Month
- **timeout:** 10
- **Sub-steps:**
  - Select Year (`web.select_option`)
    - **selector:** .react-datepicker select >> nth=1
    - **value:** ${first_day.split('-')[0]}  # Year
    - **timeout:** 10
  - Select Start Day (`web.select_option`)
    - **selector:** .react-datepicker__day--0${first_day.split('-')[2]}
    - **timeout:** 10
  - Select End Day (`web.select_option`)
    - **selector:** .react-datepicker__day--0${last_day.split('-')[2]}
    - **timeout:** 10

### 7. Search for Transfer Rates (`web.click`)
- **selector:** button.historical-btn
- **timeout:** 20
- **on_error:** retry
- **max_retries:** 2

### 8. Extract Transfer Rates (`web.get_table`)
- **selector:** table
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** {"Currency": "${currency}"}
- **min_rows:** 1
- **timeout:** 30
- **output_var:** currency_table
- **on_error:** continue

### 9. Append to Rows (`logic.append`)
- **target:** rows
- **list_var:** currency_table
- **extend:** true

### 10. Close Browser (`web.close`)

### 11. Prepare CSV Data (`logic.set_variable`)
- **name:** csv_data
- **value:** ${rows}

### 12. Write CSV File (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${csv_data}
- **columns:** Currency, Date, Buying Transfer Rate
- **encoding:** utf-8
- **append:** false
- **on_error:** retry
- **max_retries:** 2

### 13. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** ${config.output_path}
- **dry_run:** ${config.email.dry_run}
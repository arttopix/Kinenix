# Bank of Thailand Transfer Rates Report

## Variables
- `report_month`: ${config.month.date}
- `start_date`: ${date.calc(report_month, format="yyyy-MM-01")}
- `end_date`: ${date.calc(report_month, add_months=1, format="yyyy-MM-01")}
- `table_data`: []

## Steps

### 1. Calculate Report Month (`date.calc`)
- **date:** ${config.month.date}
- **format:** yyyy-MM-dd
- **add_months:** ${config.month.add_months}
- **output_var:** report_month

### 2. Calculate Start Date (`date.calc`)
- **date:** ${report_month}
- **format:** yyyy-MM-dd
- **output_var:** start_date

### 3. Calculate End Date (`date.calc`)
- **date:** ${report_month}
- **add_months:** 1
- **format:** yyyy-MM-dd
- **output_var:** end_date

### 4. Open Bank of Thailand Page (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **timeout:** 60

### 5. Accept Cookie Banner (`web.click`)
- **selector:** button[text()='Accept recommended cookies']
- **label:** Accept recommended cookies
- **optional:** true
- **timeout:** 10

### 6. Open Currency Filter (`web.click`)
- **selector:** #dropdownCurrency
- **label:** Currency filter dropdown
- **timeout:** 10

### 7. Select Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency
- **Sub-steps:**
  - Select Currency (`web.click`)
    - **selector:** .currency-filter input[name='currencyCheck'][value='${currency}']
    - **label:** Currency checkbox
    - **timeout:** 10

### 8. Set Date Range (`web.type`)
- **selector:** .react-datepicker select >> nth=0
- **label:** Month select
- **text:** ${start_date.split('-')[1]}
- **timeout:** 10
- **Sub-steps:**
  - Set Year (`web.type`)
    - **selector:** .react-datepicker select >> nth=1
    - **label:** Year select
    - **text:** ${start_date.split('-')[0]}
    - **timeout:** 10
  - Set Start Day (`web.type`)
    - **selector:** .react-datepicker__day--0${start_date.split('-')[2]}
    - **label:** Start day
    - **timeout:** 10
  - Set End Day (`web.type`)
    - **selector:** .react-datepicker__day--${end_date.split('-')[2]}
    - **label:** End day
    - **timeout:** 10

### 9. Search (`web.click`)
- **selector:** button.historical-btn
- **label:** Search button
- **timeout:** 30

### 10. Collect Table Data (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** text=${currency}
    - **label:** Currency tab
    - **timeout:** 10
  - Get Table Data (`web.get_table`)
    - **selector:** table
    - **label:** Data table
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **numeric_columns:** ["Buying Rates Transfer"]
    - **output_var:** table
  - Add Currency Column (`logic.append`)
    - **target:** table_data
    - **list_var:** table
    - **item:** {"Currency": "${currency}", "Date": "${row.Period}", "Buying Transfer Rate": ${row["Buying Rates Transfer"]}}

### 11. Write CSV File (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${table_data}
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 12. Close Browser (`web.close`)
- **(none)**

### 13. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** ${config.output_path}
- **dry_run:** ${config.email.dry_run}
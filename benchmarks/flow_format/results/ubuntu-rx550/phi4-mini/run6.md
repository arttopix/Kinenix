```markdown
# Collect Bank of Thailand Buying Transfer Rates and Email as CSV

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `config.url`: "https://www.bot.or.th/bot/bot"
- `config.currencies`: ["USD", "EUR", "JPY", "GBP"]
- `config.month.date`: "2023-04-01"
- `config.month.add_months`: 1
- `config.output_path`: "./output/bank_of_thailand_rates.csv"
- `config.headless`: true
- `config.email.to`: "recipient@example.com"
- `config.email.subject`: "Monthly Bank of Thailand Buying Transfer Rates"
- `config.email.body`: "Please find the attached monthly buying transfer rates."
- `config.email.dry_run`: false

## Steps

### 1. Calculate Report Month (`date.calc`)
- **date:** `config.month.date`
- **input_format:** "%Y-%m-%d"
- **add_months:** `config.month.add_months`
- **format:** "%Y-%m-%d"
- **output_var:** `config.month.date`

### 2. Open Bank of Thailand Website (`web.open`)
- **url:** `config.url`
- **headless:** `config.headless`
- **output_var:** `webpage`

### 3. Accept Cookie Banner (`web.click`)
- **selector:** "Accept recommended cookies button"
- **label:** "Accept recommended cookies"
- **output_var:** `webpage`

### 4. Open Currency Filter (`web.get_text`)
- **selector:** "#dropdownCurrency"
- **label:** "Currencies"
- **output_var:** `currencies`

### 5. Tick Each Currency (`logic.loop`)
- **items:** `config.currencies`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** Currency tab
    - **label:** Currency
    - **output_var:** `webpage`
  - Uncheck All Currencies (`web.uncheck`)
    - **selector:** Uncheck all checkboxes
    - **output_var:** `webpage`
  - Check Each Currency (`logic.loop`)
    - **items:** `config.currencies`
    - **item_var:** `currency`
    - **Sub-steps:**
      - Select Currency (`web.select_option`)
        - **selector:** Currency filter input
        - **label:** Currency
        - **value:** `currency`
        - **output_var:** `webpage`
      - Click Currency Checkbox (`web.click`)
        - **selector:** Checkbox for currency
        - **label:** ${currency}
        - **output_var:** `webpage`

### 6. Pick Start and End Dates (`web.get_text`)
- **selector:** Date picker
- **label:** Year, Month, Day
- **output_var:** `start_date, end_date`

### 7. Click Search Button (`web.click`)
- **selector:** "button.historical-btn"
- **label:** Historical Data Button
- **output_var:** `webpage`

### 8. Read Buying Transfer Rates (`web.get_table`)
- **selector:** Table containing buying transfer rates
- **label:** Buying Transfer Rates
- **columns:** ["Period", "Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **output_var:** `buying_transfer_rates`

### 9. Write Rates to CSV (`csv.write`)
- **file_path:** `config.output_path`
- **data:** `buying_transfer_rates`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 10. Close Browser (`web.close`)
- **output_var:** `webpage`

### 11. Email CSV File (`email.send`)
- **to:** `config.email.to`
- **subject:** `config.email.subject`
- **body:** `config.email.body`
- **on_error:** retry
- **max_retries:** 2
```
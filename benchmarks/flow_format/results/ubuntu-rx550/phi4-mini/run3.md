```markdown
# Collect Monthly Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `url`: "https://www.bot.or.th/"
- `currencies`: ["฿", "JPY", "USD", "EUR"]
- `month.date`: "01/02/2023"
- `month.add_months`: 1
- `output_path`: "output/bank_of_thailand_rates.csv"
- `headless`: true
- `email.to`: "recipient@example.com"
- `email.subject`: "Monthly Bank of Thailand Buying Transfer Rates"
- `email.body`: "Please find attached the monthly bank of Thailand buying transfer rates."
- `email.dry_run`: false

## Steps

### 1. Calculate Month Range (`date.calc`)
- **date:** "today"
- **input_format:** "dd/MM/yyyy"
- **add_months:** 1
- **snap:** true
- **format:** "dd/MM/yyyy"
- **output_var:** `config.month_range`
- **on_error:** retry
- **max_retries:** 2

### 2. Open Website and Accept Cookie Banner (`web.open`)
- **url:** ${url}
- **headless:** ${headless}
- **timeout:** 30
- **output_var:** `websession`

### 3. Select Each Currency (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Filter (`web.click`)
    - **selector:** "#dropdownCurrency"
    - **label:** "Language"
    - **on_error:** retry
    - **max_retries:** 2
  - Tick Each Currency (`web.upload_file`)
    - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **label:** "Currency"
    - **on_error:** retry
    - **max_retries:** 2

### 4. Pick Start and End Dates (`web.get_text`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Set Start Date (`web.type`)
    - **selector:** ".react-datepicker select"
    - **label:** "Year"
    - **text:** ${start_date.year}
    - **on_error:** retry
    - **max_retries:** 2
  - Set End Date (`web.type`)
    - **selector:** ".react-datepicker select"
    - **label:** "Year"
    - **text:** ${end_date.year}
    - **on_error:** retry
    - **max_retries:** 2

### 5. Search Historical Rates (`web.click`)
- **selector:** ".button.historical-btn"
- **label:** "Search"
- **output_var:** `historical_rates_page`

### 6. Extract Currency Tab Data (`web.get_table`)
- **selector:** ".currency-tab"
- **label:** "Currency"
- **columns:** "Period, Buying Rates Transfer"
- **add_columns:** "Currency"
- **min_rows:** 2
- **output_var:** `currency_data`
- **on_error:** retry
- **max_retries:** 2

### 7. Write Data to CSV (`csv.write`)
- **file_path:** ${output_path}
- **data:** ${currency_data}
- **columns:** {"Currency", "Date", "Buying Transfer Rate"}
- **encoding:** "utf-8-sig"
- **on_error:** retry
- **max_retries:** 2

### 8. Close Browser (`web.close`)
- **output_var:** `websession`

### 9. Send Email with CSV Attachment (`email.send`)
- **to:** ${email.to}
- **cc:** ""
- **bcc:** ""
- **subject:** ${email.subject}
- **body:** ${email.body}
- **html:** false
- **attachments:** [${output_path}]
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "your-email@example.com"
- **smtp_password:** "your-password"
- **use_tls:** true
- **dry_run:** ${email.dry_run}
- **on_error:** retry
- **max_retries:** 2

### 10. Retry Flow (`flow.fail`)
- **message:** "Failed to collect bank of Thailand buying transfer rates."
- **category:** "Reporting"
```
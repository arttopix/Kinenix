```markdown
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `month_start_date`: 
- `month_end_date`: 
- `output_file_path`: 
- `currencies`: 
- `email_to`: 
- `email_subject`: 
- `email_body`: 
- `email_dry_run`: 
- `session`: 

## Steps

### 1. Get Month Dates (`date.calc`)
- **date:** today
- **input_format:** "YYYY-MM-DD"
- **add_months:** -1
- **output_var:** `month_start_date`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Calculate End Date (`date.calc`):
    - **date:** ${month_start_date}
    - **add_days:** 30
    - **output_var:** `month_end_date`

### 2. Open Website (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **output_var:** `session`
- **on_error:** retry
- **max_retries:** 2

### 3. Accept Cookie Banner (`web.click`)
- **selector:** button.text('Accept recommended cookies')
- **optional:** true
- **output_var:** `session`
- **on_error:** retry
- **max_retries:** 2

### 4. Filter Currencies (`web.select_option`)
- **selector:** #dropdownCurrency
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`web.check`):
    - **selector:** .currency-filter input[name='currencyCheck'][value='${currency}']
    - **optional:** true
    - **output_var:** `session`
    - **on_error:** retry
    - **max_retries:** 2

### 5. Set Date Range (`web.select_option`)
- **selector:** .react-datepicker select >> nth=1
- **item_var:** `month`
- **Sub-steps:**
  - Set Month (`web.select_option`):
    - **selector:** .react-datepicker select >> nth=0
    - **item_var:** `day`
    - **output_var:** `session`
    - **on_error:** retry
    - **max_retries:** 2

### 6. Search (`web.click`)
- **selector:** button.historical-btn
- **optional:** true
- **output_var:** `session`
- **on_error:** retry
- **max_retries:** 2

### 7. Loop Currencies (`logic.loop`)
- **items:** ${currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Get Tab (`web.click`):
    - **selector:** currency
    - **optional:** true
    - **output_var:** `session`
    - **on_error:** retry
    - **max_retries:** 2

  - Read Table (`web.get_table`):
    - **selector:** table
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **numeric_columns:** ["Buying Rates Transfer"]
    - **add_columns:** ["Currency"]
    - **output_var:** `table`
    - **on_error:** retry
    - **max_retries:** 2

### 8. Write CSV (`csv.write`)
- **file_path:** ${output_file_path}
- **data:** `${table}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 9. Close Browser (`web.close`)
- **output_var:** `session`
- **on_error:** retry
- **max_retries:** 2

### 10. Email CSV (`email.send`)
- **to:** ${email_to}
- **subject:** ${email_subject}
- **body:** ${email_body}
- **attachments:** ${output_file_path}
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Check Dry Run (`logic.if`):
    - **condition:** ${email_dry_run}
    - **left:** true
    - **operator:** eq
    - **right:** true
    - **Sub-steps:**
      - Dry Run Message (`web.type`):
        - **selector:** body
        - **text:** This is a dry run. No email will be sent.
        - **output_var:** `session`
    - **Sub-steps:**
      - Continue (`logic.fail`):
        - **message:** Email dry run detected.
        - **category:** dry_run
```
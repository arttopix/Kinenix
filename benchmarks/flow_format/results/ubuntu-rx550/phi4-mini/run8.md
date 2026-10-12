```markdown
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `name`: `currencies`
- `date`: `<date>`
- `add_months`: `-1`
- `output_path`: `<output_path>`
- `headless`: `<headless>`
- `email.to`: `<email.to>`
- `email.subject`: `<email.subject>`
- `email.body`: `<email.body>`
- `email.dry_run`: `<email.dry_run>`

## Steps

### 1. Calculate Dates (`date.calc`)
- **date:** `<date>`
- **add_months:** `<add_months>`
- **output_var:** `config.month`
- **on_error:** retry
- **max_retries:** 2

### 2. Open Browser and Accept Cookies (`web.open`)
- **url:** `<url>`
- **headless:** `<headless>`
- **timeout:** `<timeout>`
- **on_error:** retry
- **max_retries:** 2

### 3. Select Currencies (`web.select_option`)
- **selector:** `#dropdownCurrency`
- **label:** `All Currencies`
- **value:** `<currency>`
- **ai_match:** `exact`
- **output_var:** `currencies`
- **on_error:** retry
- **max_retries:** 2

### 4. Set Up Date Picker (`web.type`)
- **selector:** `#year`
- **label:** `Year`
- **text:** `<start_date.year>`
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

- **selector:** `#month`
- **label:** `Month`
- **text:** `<start_date.month>`
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

- **selector:** `#day`
- **label:** `Day`
- **text:** `<start_date.day>`
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

### 5. Set Up End Date Picker (`web.type`)
- **selector:** `#year`
- **label:** `Year`
- **text:** `<end_date.year>`
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

- **selector:** `#month`
- **label:** `Month`
- **text:** `<end_date.month>`
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

- **selector:** `#day`
- **label:** `Day`
- **text:** `<end_date.day>`
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

### 6. Click Search Button (`web.click`)
- **selector:** `#button.historical-btn`
- **label:** `Search`
- **output_var:** `none`
- **on_error:** retry
- **max_retries:** 2

### 7. Loop through Currencies (`logic.loop`)
- **items:** `<config.currencies>`
- **item_var:** `currency`
- **Sub-steps:**
  - Select Currency (`web.select_option`)
    - **selector:** `#dropdownCurrency`
    - **label:** `All Currencies`
    - **value:** `<currency>`
    - **ai_match:** `exact`
    - **output_var:** `currencies`
    - **on_error:** retry
    - **max_retries:** 2

  - Read Table (`web.get_table`)
    - **selector:** `#currency-table`
    - **label:** `Currency Table`
    - **columns:** `["Period", "Buying Rates Transfer"]`
    - **output_var:** `currency_data`
    - **on_error:** retry
    - **max_retries:** 2

  - Append Data (`csv.write`)
    - **file_path:** `<output_path>`
    - **data:** `[[<currency>, <date>, <buying_transfer_rate>]]`
    - **columns:** `["Currency", "Date", "Buying Transfer Rate"]`
    - **on_error:** retry
    - **max_retries:** 2

### 8. Loop through Dates (`logic.loop`)
- **items:** `<config.month>`
- **item_var:** `date`
- **Sub-steps:**
  - Set Date (`web.type`)
    - **selector:** `#year`
    - **label:** `Year`
    - **text:** `<date.year>`
    - **output_var:** `date`
    - **on_error:** retry
    - **max_retries:** 2

  - Set Month (`web.type`)
    - **selector:** `#month`
    - **label:** `Month`
    - **text:** `<date.month>`
    - **output_var:** `date`
    - **on_error:** retry
    - **max_retries:** 2

  - Set Day (`web.type`)
    - **selector:** `#day`
    - **label:** `Day`
    - **text:** `<date.day>`
    - **output_var:** `date`
    - **on_error:** retry
    - **max_retries:** 2

  - Click Historical Data (`web.click`)
    - **selector:** `#button.historical-data`
    - **label:** `Historical Data`
    - **output_var:** `none`
    - **on_error:** retry
    - **max_retries:** 2

  - Read Table (`web.get_table`)
    - **selector:** `#currency-data`
    - **label:** `Currency Data`
    - **columns:** `["Period", "Buying Rates Transfer"]`
    - **output_var:** `date_data`
    - **on_error:** retry
    - **max_retries:** 2

  - Append Data (`csv.write`)
    - **file_path:** `<output_path>`
    - **data:** `[[<currency>, <date>, <buying_transfer_rate>]]`
    - **columns:** `["Currency", "Date", "Buying Transfer Rate"]`
    - **on_error:** retry
    - **max_retries:** 2

### 9. Close Browser (`web.close`)
- **output_var:** `none`
- **on_error:** continue
- **max_retries:** 2

### 10. Send Email (`email.send`)
- **to:** `<email.to>`
- **cc:** `none`
- **bcc:** `none`
- **subject:** `<email.subject>`
- **body:** `<email.body>`
- **html:** `none`
- **attachments:** `none`
- **smtp_host:** `none`
- **smtp_port:** `none`
- **smtp_user:** `none`
- **smtp_password:** `none`
- **use_tls:** `none`
- **dry_run:** `<email.dry_run>`
- **on_error:** retry
- **max_retries:** 2
```
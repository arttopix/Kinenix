```markdown
# Collect Monthly Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `name`: "Collect Monthly Bank of Thailand Buying Transfer Rates"
- `config.url`: "https://www.bot.co.th/eng/btt/"
- `config.currencies`: "THB,USD,JPY,KRW"
- `config.month.date`: "2023-04-01"
- `config.month.add_months`: 1
- `config.output_path`: "monthly_rates.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Monthly Buying Transfer Rates"
- `config.email.body`: "Please find the monthly buying transfer rates for selected currencies."
- `config.headless`: true
- `config.dry_run`: false

## Steps

### 1. Calculate Report Month (`date.calc`)
- **date:** "{{config.month.date}}"
- **input_format:** "YYYY-MM-DD"
- **add_months:** -1
- **output_var:** `report_start_date`
- **on_error:** retry
- **max_retries:** 2

### 2. Open Website and Accept Cookie Banner (`web.open`)
- **url:** `{{config.url}}`
- **headless:** true
- **on_error:** retry
- **max_retries:** 2

### 3. Filter Currencies (`web.check`, `web.select_option`)
- **selector:** "#dropdownCurrency"
- **label:** "Select Currencies"
- **output_var:** `currencies_checked`
- **on_error:** retry
- **max_retries:** 2

### 4. Filter Currencies by Value (`web.check`, `web.select_option`)
- **selector:** "#currency-filter"
- **label:** "Currency Filter"
- **output_var:** `currencies_selected`
- **on_error:** retry
- **max_retries:** 2

### 5. Pick Start and End Dates (`web.click`, `web.select_option`)
- **selector:** ".start-date-picker"
- **label:** "Start Date"
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

- **selector:** ".end-date-picker"
- **label:** "End Date"
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

### 6. Search Historical Rates (`web.click`, `web.click`)
- **selector:** ".button.historical-btn"
- **output_var:** `historical_rates_page`
- **on_error:** retry
- **max_retries:** 2

### 7. Loop Through Currencies (`logic.loop`)
- **items:** `{{config.currencies}}`
- **item_var:** `currencies`
- **Sub-steps:**
  - Check Currency Tab (`web.check`, `web.select_option`)
    - **selector:** "#currency-tab"
    - **label:** "Currency Tab"
    - **output_var:** `currency_tab_checked`
    - **on_error:** retry
    - **max_retries:** 2

  - Read Currency Table (`web.get_table`)
    - **selector:** "#currency-table"
    - **label:** "Currency Table"
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **output_var:** `currency_data`
    - **on_error:** retry
    - **max_retries:** 2

  - Add Currency Column (`logic.append`)
    - **target:** `currency_data`
    - **item:** `["Currency", "Date", "Buying Transfer Rate"]`

  - Write to CSV (`csv.write`)
    - **file_path:** `{{config.output_path}}`
    - **data:** `{{currency_data}}`
    - **on_error:** retry
    - **max_retries:** 2

### 8. Email CSV File (`email.send`)
- **to:** `{{config.email.to}}`
- **cc:** null
- **bcc:** null
- **subject:** `{{config.email.subject}}`
- **body:** `{{config.email.body}}`
- **html:** false
- **attachments:** `{{config.output_path}}`
- **smtp_host:** null
- **smtp_port:** null
- **smtp_user:** null
- **smtp_password:** null
- **use_tls:** null
- **dry_run:** false
- **on_error:** retry
- **max_retries:** 2
```
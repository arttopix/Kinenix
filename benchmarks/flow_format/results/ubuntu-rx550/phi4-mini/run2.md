```markdown
# Bank of Thailand Buying Transfer Rates Report

> Collects Bank of Thailand buying transfer rates for several currencies over one month and emails them as a CSV file.

## Variables
- `name`: "report_monthly_rates"
- `config`: [See below for config details]

## Config
- `url`: "https://www.bogth.com/eng/eng/index.aspx"
- `currencies`: ["฿", "¥", "€", "₽", "£", "¥", "₹", "₩"]
- `month.date`: "today"
- `month.add_months`: -1
- `output_path`: "./reports/monthly_rates.csv"
- `headless`: true
- `email.to`: "recipient@example.com"
- `email.subject`: "Monthly Buying Transfer Rates Report"
- `email.body`: "Attached is the monthly buying transfer rates report."
- `email.dry_run`: false

## Steps

### 1. Calculate report month (`date.calc`)
- **date:** `config.month.date`
- **input_format:** "YYYY-MM-DD"
- **add_months:** `config.month.add_months`
- **format:** "YYYY-MM"
- **output_var:** `config.report_month_start`
- **output_var2:** `config.report_month_end`
- **on_error:** retry
- **max_retries:** 2

### 2. Open Bank of Thailand website (`web.open`)
- **url:** `config.url`
- **headless:** `config.headless`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Accept cookie banner (`web.click`)
    - **selector:** "Accept recommended cookies"
    - **label:** "Accept recommended cookies"
- **Sub-step:** retry if button not found

### 3. Filter currencies (`web.check` and `web.select_option`)
- **items:** `config.currencies`
- **item_var:** "currency"
- **Sub-steps:**
  - Check if currency filter is visible (`web.check`)
    - **selector:** ".currency-filter"
    - **label:** "Currency Filter"
    - **on_error:** retry
- **Sub-step:**
  - Select currency (`web.select_option`)
    - **selector:** ".dropdownCurrency"
    - **label:** "Currency"
    - **value:** "${currency}"
    - **ai_match:** "currency"
- **Sub-step:** retry if currency not found

### 4. Set start and end dates (`web.get_text` and `date.calc`)
- **text:** "Start and end dates"
- **output_var:** `config.start_date`
- **text:** "End date"
- **output_var2:** `config.end_date`
- **on_error:** retry
- **max_retries:** 2

### 5. Search for rates (`web.click` and `web.get_table`)
- **selector:** "button.historical-btn"
- **label:** "Historical Rates"
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Get table of results (`web.get_table`)
    - **selector:** ".historical-rates"
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **min_rows:** 1
    - **output_var:** `config.rates_data`
- **Sub-step:** retry if table not found

### 6. Process rates data (`logic.loop`)
- **items:** `config.currencies`
- **item_var:** "currency"
- **Sub-steps:**
  - Loop through each currency (`logic.loop`)
    - **items:** `config.currencies`
    - **item_var:** "currency"
    - **Sub-step:**
      - Read table (`web.get_table`)
        - **selector:** ".historical-rates"
        - **columns:** ["Period", "Buying Rates Transfer"]
        - **min_rows:** 1
        - **output_var:** `config.rates_for_currency`
- **Sub-step:** retry if table not found

### 7. Write data to CSV (`csv.write`)
- **file_path:** `config.output_path`
- **data:** `config.rates_data`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 8. Email CSV report (`email.send`)
- **to:** `config.email.to`
- **cc:** ""
- **bcc:** ""
- **subject:** `config.email.subject`
- **body:** `config.email.body`
- **html:** false
- **attachments:** [config.output_path]
- **smtp_host:** ""
- **smtp_port:** ""
- **smtp_user:** ""
- **smtp_password:** ""
- **use_tls:** false
- **dry_run:** `config.email.dry_run`
- **on_error:** retry
- **max_retries:** 2

# End of Flow
```
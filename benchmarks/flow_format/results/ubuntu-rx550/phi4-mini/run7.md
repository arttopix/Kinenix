```markdown
# Collect Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `url`: [Bank of Thailand Currency Rates](https://www.bot.or.th/monetary-policy/bank-of-thailand-currency-rates/)
- `currencies`: ["USD", "EUR", "GBP", "JPY", "CNY"]
- `month.date`: "2023-03-01"
- `month.add_months`: -1
- `output_path`: "./buying_transfer_rates.csv"
- `headless`: true
- `email.to`: "recipient@example.com"
- `email.subject`: "Monthly Buying Transfer Rates"
- `email.body`: "Attached is the CSV file with the buying transfer rates for the specified currencies."
- `email.dry_run`: false

## Steps

### 1. Calculate report month (`date.calc`)
- **date:** `${config.month.date}`
- **add_months:** `${config.month.add_months}`
- **output_var:** `config.month.date`

### 2. Open Bank of Thailand page (`web.open`)
- **url:** `${url}`
- **headless:** `${config.headless}`
- **output_var:** `browser`

### 3. Accept cookie banner (`web.click`)
- **selector:** "Accept recommended cookies button"
- **output_var:** `cookie_accepted`

### 4. Open currency filter (`web.check`)
- **selector:** "#dropdownCurrency"
- **label:** "Currency Filter"
- **output_var:** `currency_filter_checked`

### 5. Select each currency (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** "Currency tab button"
    - **output_var:** `currency_tab_opened`
  - Tick each currency (`web.uncheck`)
    - **selector:** "Checkbox for ${currency}"
    - **output_var:** `currency_checked`
  - Pick start date (`date.pick`)
    - **date:** "Start Date"
    - **output_var:** `start_date`
  - Pick end date (`date.pick`)
    - **date:** "End Date"
    - **output_var:** `end_date`
  - Click search button (`web.click`)
    - **selector:** "Search Button"
    - **output_var:** `search_button_clicked`

### 6. Extract rates (`web.get_table`)
- **selector:** "Table with rates"
- **label:** "Rates Table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **output_var:** `buying_transfer_rates`

### 7. Write to CSV (`csv.write`)
- **file_path:** `${output_path}`
- **data:** `buying_transfer_rates`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 8. Close browser (`web.close`)

### 9. Email CSV (`email.send`)
- **to:** `${config.email.to}`
- **cc:** null
- **bcc:** null
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **html:** false
- **attachments:** `${output_path}`
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** true
- **dry_run:** false
```
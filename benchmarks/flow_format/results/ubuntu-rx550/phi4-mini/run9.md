```markdown
# Collect Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `config.url`: "https://www.bot.or.th/bot/"
- `config.currencies`: ["฿", "€", "₽", "¥", "₱", "₨", "₪"]
- `config.month.date`: "today"
- `config.month.add_months`: "-1"
- `config.output_path`: "./output/bot_rates.csv"
- `config.headless`: true
- `config.email.to`: "your-email@example.com"
- `config.email.subject`: "Monthly Bot Thailand Buying Transfer Rates"
- `config.email.body`: "Please find attached the latest Bot Thailand buying transfer rates."
- `config.dry_run`: false

## Steps

### 1. Calculate the first and last day of the report month (`date.calc`)
- **date:** `${config.month.date}`
- **input_format:** "YYYY-MM-DD"
- **add_months:** `${config.month.add_months}`
- **snap:** "first"
- **format:** "YYYY-MM-DD"
- **output_var:** `start_date`
- **output_var_last`: `end_date`

### 2. Open the Bot Thailand website (`web.open`)
- **url:** `${config.url}`
- **headless:** `${config.headless}`
- **timeout:** 10
- **output_var:** `website`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 3. Accept the cookie banner (`web.click`)
- **selector:** ".accept-cookies-button"
- **label:** "Accept recommended cookies"
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 4. Open the currency filter (`web.check`)
- **selector:** "#dropdownCurrency"
- **label:** "Currency Filter"
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 5. Tick each currency in the filter (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`web.uncheck`):
    - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **label:** "Uncheck ${currency}"
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
  - Check Currency (`web.check`)
    - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **label:** "Check ${currency}"
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5

### 6. Pick the start and end dates in the date picker (`web.get_text`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **output_var:** `start_year`
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **Sub-steps:**
  - Get Year (`web.get_text`)
    - **selector:** ".react-datepicker select >> nth=1"
    - **output_var:** `start_year`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
- **Sub-steps:**
  - Get Month (`web.get_text`)
    - **selector:** ".react-datepicker select >> nth=0"
    - **output_var:** `start_month`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
- **Sub-steps:**
  - Get Day (`web.get_text`)
    - **selector:** ".react-datepicker [type='number']"
    - **output_var:** `start_day`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
- **Sub-steps:**
  - Get Year (`web.get_text`)
    - **selector:** ".react-datepicker select >> nth=1"
    - **output_var:** `end_year`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
- **Sub-steps:**
  - Get Month (`web.get_text`)
    - **selector:** ".react-datepicker select >> nth=0"
    - **output_var:** `end_month`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
- **Sub-steps:**
  - Get Day (`web.get_text`)
    - **selector:** ".react-datepicker [type='number']"
    - **output_var:** `end_day`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5

### 7. Click the 'button.historical-btn' to search (`web.click`)
- **selector:** ".button.historical-btn"
- **label:** "Historical Data"
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 8. Read the visible table for each currency (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`)
    - **selector:** `div.currency-tab-button-for-${currency}`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
  - Get Table (`web.get_table`)
    - **columns:** ["Period", "Buying Rates Transfer"]
    - **add_columns:** {"Currency": "Currency", "Date": "Date", "Buying Transfer Rate": "Buying Transfer Rate"}
    - **min_rows:** 2
    - **output_var:** `currency_data`
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5

### 9. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `currency_data`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8-sig"
- **append:** false
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 10. Email the CSV to ${config.email.to} (`email.send`)
- **to:** `${config.email.to}`
- **cc:** ""
- **bcc:** ""
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **html:** false
- **attachments:** true
- **attachments_path:** `${config.output_path}`
- **smtp_host:** ""
- **smtp_port:** ""
- **smtp_user:** ""
- **smtp_password:** ""
- **use_tls:** false
- **dry_run:** false
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
```
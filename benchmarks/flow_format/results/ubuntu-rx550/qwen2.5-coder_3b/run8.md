# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: {"url": "https://www.bangkokbank.co.th/en/financial-info/foreign-currency-exchange-rate", "currencies": ["THB", "USD", "EUR", "JPY"], "month": {"date": "today", "add_months": -1}, "output_path": "bank_of_thailand_btc_rates.csv", "headless": true, "email": {"to": "example@example.com", "subject": "Bank of Thailand Buying Transfer Rates", "body": "Please find the attached CSV file."}}
- `start_date`: ""
- `end_date`: ""
- `report_date`: ""
- `dates`: []
- `exchange_rates`: []
- `rows`: []

## Steps

### 1. Get Report Month (`date.calc`)
- **date:** `${config.month.date}`
- **input_format:** "%Y-%m-%d"
- **add_months:** ${config.month.add_months}
- **snap:** "day"
- **format:** "%Y-%m-%d"
- **output_var:** `report_date`
- **on_error:** retry
- **max_retries:** 2

### 2. Get Start and End Dates (`date.calc`)
- **date:** `${report_date}`
- **input_format:** "%Y-%m-%d"
- **add_days:** -1
- **format:** "%Y-%m-%d"
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

- **date:** `${report_date}`
- **input_format:** "%Y-%m-%d"
- **add_days:** 31
- **format:** "%Y-%m-%d"
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

### 3. Open URL and Accept Cookies (`web.open`)
- **url:** `${config.url}`
- **headless:** ${config.headless}
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 4. Accept Cookie Banner (`web.click`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Accept recommended cookies"
- **output_var:** "cookie_accepted"
- **on_error:** retry
- **max_retries:** 2

- **condition:** "${cookie_accepted}" != "true"
- **on_error:** retry
- **max_retries:** 2

### 5. Open Currency Filter (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **label:** "Currency"
- **value:** ""
- **text:** "All currencies"
- **output_var:** "currency_filter"
- **on_error:** retry
- **max_retries:** 2

- **condition:** "${currency_filter}" != "All currencies"
- **on_error:** retry
- **max_retries:** 2

- **logic.loop:** "${config.currencies}"
  - **item_var:** "currency"
  - **Sub-steps:**
    - Select Currency (`web.select_option`):
      - **selector:** "#dropdownCurrency"
      - **label:** "Currency"
      - **value:** "${currency}"
      - **text:** "${currency}"
      - **output_var:** "currency_selected"
      - **on_error:** retry
      - **max_retries:** 2

### 6. Set Start and End Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **value:** "${start_date:year}"
- **text:** "${start_date:year}"
- **output_var:** "year_selected"
- **on_error:** retry
- **max_retries:** 2

- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **value:** "${start_date:month}"
- **text:** "${start_date:month}"
- **output_var:** "month_selected"
- **on_error:** retry
- **max_retries:** 2

- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **value:** "${end_date:year}"
- **text:** "${end_date:year}"
- **output_var:** "year_selected"
- **on_error:** retry
- **max_retries:** 2

- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **value:** "${end_date:month}"
- **text:** "${end_date:month}"
- **output_var:** "month_selected"
- **on_error:** retry
- **max_retries:** 2

### 7. Search for Exchange Rates (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **output_var:** "searched"
- **on_error:** retry
- **max_retries:** 2

- **condition:** "${searched}" != "true"
- **on_error:** retry
- **max_retries:** 2

### 8. Collect Exchange Rates (`web.get_table`)
- **selector:** "table.exchange-rate-table"
- **label:** "Exchange Rates"
- **columns:** ["Date", "Buying Transfer Rate"]
- **numeric_columns:** ["Buying Transfer Rate"]
- **add_columns:** ["Currency"]
- **min_rows:** 0
- **output_var:** "exchange_rates"
- **on_error:** retry
- **max_retries:** 2

- **logic.loop:** "${exchange_rates}"
  - **item_var:** "rate"
  - **Sub-steps:**
    - Add Date (`web.get_attribute`):
      - **selector:** "table.exchange-rate-table"
      - **label:** "Exchange Rates"
      - **attribute:** "data-date"
      - **name:** "date"
      - **output_var:** "rate_date"
      - **on_error:** retry
      - **max_retries:** 2

    - Add Buying Transfer Rate (`web.get_attribute`):
      - **selector:** "table.exchange-rate-table"
      - **label:** "Exchange Rates"
      - **attribute:** "data-buying-amount"
      - **name:** "buying_transfer_rate"
      - **output_var:** "rate_buying_transfer_rate"
      - **on_error:** retry
      - **max_retries:** 2

    - Add Currency (`web.get_attribute`):
      - **selector:** "table.exchange-rate-table"
      - **label:** "Exchange Rates"
      - **attribute:** "data-currency"
      - **name:** "currency"
      - **output_var:** "rate_currency"
      - **on_error:** retry
      - **max_retries:** 2

    - Add Row (`logic.append`):
      - **target:** rows
      - **item:** {"Date": "${rate_date}", "Buying Transfer Rate": "${rate_buying_transfer_rate}", "Currency": "${rate_currency}"}
      - **on_error:** retry
      - **max_retries:** 2

### 9. Write CSV to File (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${rows}
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 10. Close Browser (`web.close`)
- **(none)**

### 11. Email CSV (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **html:** false
- **attachments:** ${config.output_path}
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** true
- **dry_run:** ${config.email.dry_run}
- **output_var:** "email_sent"
- **on_error:** retry
- **max_retries:** 2

- **condition:** "${email_sent}" != "true"
- **on_error:** retry
- **max_retries:** 2
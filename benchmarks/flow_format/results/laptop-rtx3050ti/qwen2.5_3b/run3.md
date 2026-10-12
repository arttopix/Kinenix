# Collect Bank of Thailand Transfer Rates

## Variables
- `config.month.date`: today
- `config.month.add_months`: -1
- `config.currencies`: ["THB", "USD", "EUR"]
- `config.url`: "https://www.bangkokbank.com/foreign-exchange/foreign-exchange-rates/"
- `config.output_path`: "./output/transfer_rates.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Transfer Rates Report"
- `config.email.body`: "Please find attached the Bank of Thailand transfer rates report for the month of ${config.month.date}."
- `config.email.dry_run`: false

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** "${config.month.add_months}"
- **output_var:** `report_month_range`
- **on_error:** retry
- **max_retries:** 2

### 2. Open ${config.url}; accept the cookie banner if it appears (button text 'Accept recommended cookies') (`web.click`)
- **selector:** "button[aria-label='Accept recommended cookies']"
- **label:** "Accept recommended cookies"
- **optional:** false
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **web.click:** ${report_month_range}
  - **web.click:** ${report_month_range}

### 3. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "Currency Filter"
- **optional:** false
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **logic.loop:**
    - **items:** `${config.currencies}`
    - **item_var:** `currency`
    - **Sub-steps:**
      - **web.click:** `.currency-filter input[name='currencyCheck'][value='${currency}']`

### 4. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.type`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **optional:** false
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **web.type:** "${report_month_range.year}"
- **Sub-steps:**
  - **selector:** ".react-datepicker select >> nth=0"
  - **label:** "Month"
  - **optional:** false
  - **timeout:** 10
  - **on_error:** retry
  - **max_retries:** 2
  - **Sub-steps:**
    - **web.type:** "${report_month_range.month}"
- **Sub-steps:**
  - **selector:** ".react-datepicker select >> nth=2"
  - **label:** "Day"
  - **optional:** false
  - **timeout:** 10
  - **on_error:** retry
  - **max_retries:** 2
  - **Sub-steps:**
    - **web.type:** "${report_month_range.day}"

### 5. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **optional:** false
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2

### 6. For each currency, click its tab button (text = currency) and read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (`web.click`)
- **selector:** ".currency-tab"
- **label:** "Currency Tab"
- **optional:** false
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **web.click:** "button[aria-label='${currency}']"
- **Sub-steps:**
  - **web.get_table:** ".exchange-table"
  - **columns:** ["Period", "Buying Rates Transfer"]
  - **numeric_columns:** ["Buying Rates Transfer"]
  - **add_columns:** ["Currency"]
  - **min_rows:** 1
  - **timeout:** 10
  - **on_error:** retry
  - **max_retries:** 2
  - **Sub-steps:**
    - **logic.loop:**
      - **items:** `${table.rows}`
      - **item_var:** `row`
      - **Sub-steps:**
        - **logic.append:**
          - **target:** `rows`
          - **item:** {
            "Currency": "${row.Currency}",
            "Date": "${row.Period}",
            "Buying Transfer Rate": "${row.Buying Rates Transfer}"
          }

### 7. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **web.screenshot:** "./output/transfer_rates.png"

### 8. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}) (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** false
- **attachments:** [".output/transfer_rates.csv"]
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** true
- **dry_run:** "${config.email.dry_run}"
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **web.screenshot:** "./output/transfer_rates_email.png"
  - **web.open:** "https://smtp.example.com/"
  - **web.type:** "input#email"
  - **web.type:** "input#password"
  - **web.press:** "button#login"
  - **web.type:** "input#attachment"
  - **web.press:** "button#send"
  - **web.screenshot:** "./output/transfer_rates_email_sent.png"

### 9. Clean up (`file.delete`)
- **path:** "./output/*.csv"
- **overwrite:** true
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **file.delete:** "./output/*.png"
  - **overwrite:** true
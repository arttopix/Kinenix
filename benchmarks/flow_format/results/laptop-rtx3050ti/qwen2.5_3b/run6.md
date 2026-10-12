# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: <initial value>
- `config.month`: {"date": "today", "add_months": -1}
- `config.currencies`: ["THB", "USD", "EUR"]
- `config.url`: <initial value>
- `config.output_path`: <initial value>
- `config.email.to`: <initial value>
- `config.email.subject`: <initial value>
- `config.email.body`: <initial value>
- `config.email.dry_run`: False

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** "${config.month.add_months}"
- **add_days:** 0
- **output_var:** `report_month`
- **on_error:** continue
- **max_retries:** 2
- **Sub-steps:**
  - **set_variable:** `report_month_start` (`date.calc`)

### 2. Open ${config.url}; accept the cookie banner if it appears (`web.open`)
- **url:** "${config.url}"
- **headless:** "${config.headless}"
- **timeout:** 60
- **Sub-steps:**
  - **web.is_visible:** `button.accept-recommended-cookies`, `Accept recommended cookies`
  - **web.press:** `button.accept-recommended-cookies`, `Accept recommended cookies`

### 3. Open the currency filter (`web.select_option`)
- **selector:** `#dropdownCurrency`
- **label:** `#dropdownCurrency`
- **value:** "${config.currencies}"
- **text:** "${config.currencies}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

### 4. Pick the start and end dates in the date picker (`web.select_option`)
- **selector:** `#start_date`
- **label:** `#start_date`
- **value:** "${report_month_start}"
- **text:** "${report_month_start}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

- **selector:** `#end_date`
- **label:** `#end_date`
- **value:** "${report_month}"
- **text:** "${report_month}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

### 5. Click 'button.historical-btn' to search (`web.click`)
- **selector:** `button.historical-btn`
- **label:** `button.historical-btn`

### 6. For each currency, click its tab button (`logic.loop`)
- **items:** "${config.currencies}"
- **item_var:** `currency`
- **Sub-steps:**
  - **web.is_visible:** `a[data-currency="${currency}"]`, `a[data-currency="${currency}"]`
  - **web.click:** `a[data-currency="${currency}"]`, `a[data-currency="${currency}"]`

### 7. Read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (`web.get_table`)
- **selector:** `table`
- **label:** `table`
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **timeout:** 60
- **Sub-steps:**
  - **logic.append:** `rows`, `n`, `results`, {"Currency": "${currency}", "Date": "${row['Period']}", "Buying Transfer Rate": "${row['Buying Rates Transfer']}"}, False

### 8. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** False

### 9. Close the browser (`web.close`)

### 10. Email the CSV to ${config.email.to} (subject ${config.email.subject}) (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** False
- **attachments:** "${config.output_path}"
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** True
- **dry_run:** "${config.email.dry_run}"

### 11. Screenshot (`web.screenshot`)
- **path:** "${config.output_path}/report.png"
- **full_page:** True

### 12. Save the screenshot to the output path (`file.write_text`)
- **path:** "${config.output_path}/report.png"
- **content:** "${config.output_path}/report.png"
- **append:** False

### 13. Open the browser and start again (`web.open`)
- **url:** "${config.url}"
- **headless:** "${config.headless}"
- **timeout:** 60

### 14. Open the currency filter (`web.select_option`)
- **selector:** `#dropdownCurrency`
- **label:** `#dropdownCurrency`
- **value:** "${config.currencies}"
- **text:** "${config.currencies}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

### 15. Pick the start and end dates in the date picker (`web.select_option`)
- **selector:** `#start_date`
- **label:** `#start_date`
- **value:** "${report_month_start}"
- **text:** "${report_month_start}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

- **selector:** `#end_date`
- **label:** `#end_date`
- **value:** "${report_month}"
- **text:** "${report_month}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"

### 16. Click 'button.historical-btn' to search (`web.click`)
- **selector:** `button.historical-btn`
- **label:** `button.historical-btn`

### 17. For each currency, click its tab button (`logic.loop`)
- **items:** "${config.currencies}"
- **item_var:** `currency`
- **Sub-steps:**
  - **web.is_visible:** `a[data-currency="${currency}"]`, `a[data-currency="${currency}"]`
  - **web.click:** `a[data-currency="${currency}"]`, `a[data-currency="${currency}"]`

### 18. Read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (`web.get_table`)
- **selector:** `table`
- **label:** `table`
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **timeout:** 60
- **Sub-steps:**
  - **logic.append:** `rows`, `n`, `results`, {"Currency": "${currency}", "Date": "${row['Period']}", "Buying Transfer Rate": "${row['Buying Rates Transfer']}"}, False

### 19. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** False

### 20. Close the browser (`web.close`)

### 21. Email the CSV to ${config.email.to} (subject ${config.email.subject}) (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** False
- **attachments:** "${config.output_path}"
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** True
- **dry_run:** "${config.email.dry_run}"

### 22. Screenshot (`web.screenshot`)
- **path:** "${config.output_path}/report.png"
- **full_page:** True

### 23. Save the screenshot to the output path (`file.write_text`)
- **path:** "${config.output_path}/report.png"
- **content:** "${config.output_path}/report.png"
- **append:** False
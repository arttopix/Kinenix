# Collect Bank of Thailand Transfer Rates

## Variables
- `base_url`: ${config.url}
- `currencies`: ${config.currencies}
- `month.date`: ${config.month.date}
- `month.add_months`: ${config.month.add_months}
- `output_path`: ${config.output_path}
- `email.to`: ${config.email.to}
- `email.subject`: ${config.email.subject}
- `email.body`: ${config.email.body}
- `email.dry_run`: ${config.email.dry_run}
- `config.month`: {"date": "${month.date}", "add_months": "${month.add_months}"}
- `config.currencies`: ["currency1", "currency2", "currency3"]
- `config.output_path`: "./output/transfers.csv"
- `config.email.to`: "recipient@example.com"
- `config.email.subject`: "Bank of Thailand Transfer Rates for ${month.date} to ${month.date + month.add_months}"
- `config.email.body`: "Attached is the CSV file with Bank of Thailand transfer rates for ${month.date} to ${month.date + month.add_months}."
- `config.headless`: true
- `config.email.dry_run`: false

## Steps

### 1. Determine Date Range (`date.calc`)
- **date:** "${month.date}"
- **input_format:** "date"
- **add_months:** "${month.add_months}"
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **start_date:** `${date.calc(date, "date", "${month.date}", "${month.add_months}")}`

### 2. Open Browser (`web.open`)
- **url:** "${base_url}"
- **headless:** ${config.headless}
- **timeout:** 60
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 3. Accept Cookie Banner (`web.click`)
- **selector:** ".react-cookie-banner button:contains('Accept recommended cookies')"
- **label:** "Accept recommended cookies"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 4. Set Currency Filters (`web.select_option`)
- **selector:** ".currency-filter input[name='currencyCheck']:contains('currency1')"
- **label:** "currency1"
- **value:** "currency1"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **currency1:** "currency1"

- **selector:** ".currency-filter input[name='currencyCheck']:contains('currency2')"
- **label:** "currency2"
- **value:** "currency2"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **currency2:** "currency2"

- **selector:** ".currency-filter input[name='currencyCheck']:contains('currency3')"
- **label:** "currency3"
- **value:** "currency3"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **currency3:** "currency3"

### 5. Select Start and End Dates (`web.select_option`)
- **selector:** ".react-datepicker select:contains('Year')"
- **label:** "Year"
- **value:** "${start_date.year}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **year:** "${start_date.year}"

- **selector:** ".react-datepicker select:contains('Month')"
- **label:** "Month"
- **value:** "${start_date.month}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **month:** "${start_date.month}"

- **selector:** ".react-datepicker input:contains('Day')"
- **label:** "Day"
- **value:** "${start_date.day}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **day:** "${start_date.day}"

### 6. Click Historical Button (`web.click`)
- **selector:** ".historical-btn"
- **label:** "Historical"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 7. Get Table Data (`web.get_table`)
- **selector:** ".table tbody"
- **label:** "Table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **output_var:** `table_data`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **table:** `${web.get_table(selector, "Table", columns, numeric_columns, add_columns, min_rows, timeout)}`

### 8. Add Rows to CSV (`csv.write`)
- **file_path:** "${output_path}"
- **data:** `table_data`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** true
- **output_var:** `csv_data`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - **csv:** `${csv.write(file_path, data, columns, encoding, append)}`

### 9. Close Browser (`web.close`)
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 10. Send Email (`email.send`)
- **to:** "${email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **attachments:** [`${csv_data}`]
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** true
- **dry_run:** ${config.email.dry_run}
- **output_var:** `email_sent`
- **on_error:** retry
- **max_retries:** 2

### 11. Log Completion (`logic.set_variable`)
- **name:** `status`
- **value:** "Data collected and email sent successfully."
- **output_var:** `status`
- **on_error:** continue

### 12. Return Result (`flow.return`)
- **value:** `status`
- **output_var:** `status`
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: <initial value>
- `config.url`: <initial value>
- `config.currencies`: []
- `config.month.date`: "today"
- `config.month.add_months`: -1
- `config.output_path`: ""
- `config.email.to`: ""
- `config.email.subject`: ""
- `config.email.body`: ""
- `config.email.dry_run`: False

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** "${config.month.add_months}"
- **output_var:** `report_dates`

### 2. Open ${config.url}; accept the cookie banner if it appears (`web.click`)
- **selector:** ".react-cookie-banner button[text='Accept recommended cookies']"
- **label:** "Accept recommended cookies"
- **optional:** True
- **output_var:** `page_opened`
- **on_error:** retry
- **max_retries:** 2

### 3. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.click`)
- **selector:** "#dropdownCurrency input"
- **label:** "input"
- **value:** "${item}"
- **output_var:** `currencies_ticked`

### 4. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.type`)
- **selector:** ".react-datepicker input[aria-label='Pick a date using keyboard arrows, or your cursor to edit']"
- **label:** "input"
- **text:** "${report_dates.first_day}"
- **output_var:** `start_date_selected`
- **on_error:** retry
- **max_retries:** 2

### 5. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **output_var:** `search_clicked`

### 6. For each currency, click its tab button (text = currency) and read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (a number), add a Currency column (`web.click`)
- **selector:** ".currency-tab"
- **label:** "${item}"
- **output_var:** `currency_tab_clicked`

### 7. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** False
- **output_var:** `csv_written`

### 8. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}) (`email.send`)
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
- **output_var:** `email_sent`

### 9. Retry opening the page and searching (`web.open`)
- **url:** "${config.url}"
- **headless:** False
- **output_var:** `page_opened_retry`
- **on_error:** retry
- **max_retries:** 2

### 10. Retry writing the CSV (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** False
- **output_var:** `csv_written_retry`

### 11. Retry email the CSV (`email.send`)
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
- **output_var:** `email_sent_retry`

### 12. Screenshot (`web.screenshot`)
- **path:** "./report.png"
- **full_page:** True

### 13. Store the screenshot (`file.write_text`)
- **path:** "./report.png"
- **content:** "${report.png}"
- **append:** False
- **encoding:** "base64"

### 14. End (`logic.set_variable`)
- **name:** `status`
- **value:** "success"
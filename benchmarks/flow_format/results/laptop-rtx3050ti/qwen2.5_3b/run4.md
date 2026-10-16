# Collect Bank of Thailand Transfer Rates

## Variables
- `config`: <initial value>
- `rows`: []

## Steps

### 1. Get Report Month (`date.calc`)
- **date:** "today"
- **input_format:** "%Y-%m-%d"
- **add_months:** -1
- **output_var:** `config.month`

### 2. Open Kinenix (`web.open`)
- **url:** "${config.url}"
- **headless:** True
- **timeout:** 60
- **output_var:** `browser`

### 3. Accept Cookies Banner (`web.click`)
- **selector:** ".react-cookie-banner button"
- **label:** "Accept recommended cookies"
- **optional:** False
- **timeout:** 60
- **output_var:** `browser`

### 4. Set Currencies (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **label:** "${config.currencies}"
- **value:** "${n}"
- **text:** "${n}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"
- **systemone_url:** False
- **fallback_to_ollama:** False
- **timeout:** 60
- **output_var:** `browser`

### 5. Set Date (`web.select_option`)
- **selector:** "input[name='month']"
- **label:** "${config.month.date}"
- **text:** "${config.month.date}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"
- **systemone_url:** False
- **fallback_to_ollama:** False
- **timeout:** 60
- **output_var:** `browser`

- **selector:** "input[name='day']"
- **label:** "${config.month.date}"
- **text:** "${config.month.date}"
- **index:** 0
- **ai_match:** False
- **base_url:** "${config.url}"
- **systemone_url:** False
- **fallback_to_ollama:** False
- **timeout:** 60
- **output_var:** `browser`

### 6. Click Search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **optional:** False
- **timeout:** 60
- **output_var:** `browser`

### 7. Read Data (`web.get_table`)
- **selector:** "table"
- **label:** "table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **timeout:** 60
- **output_var:** `data`

### 8. Append Data to Rows (`logic.append`)
- **target:** `rows`
- **item:** `data`

### 9. Close Browser (`web.close`)
- **selector:** "button.close"
- **label:** "button.close"
- **optional:** True
- **timeout:** 60
- **output_var:** `browser`

### 10. Convert Rows to CSV (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **append:** False
- **output_var:** `csv_file`

### 11. Email CSV (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** False
- **attachments:** [`${csv_file}`]
- **smtp_host:** "${config.email.smtp_host}"
- **smtp_port:** "${config.email.smtp_port}"
- **smtp_user:** "${config.email.smtp_user}"
- **smtp_password:** "${config.email.smtp_password}"
- **use_tls:** "${config.email.use_tls}"
- **dry_run:** "${config.email.dry_run}"
- **output_var:** `email_result`

### 12. Handle Errors (`flow.fail`)
- **message:** "Failed to collect and email transfer rates. Please check the configuration and retry."
- **category:** "error"

### 13. Return Result (`flow.return`)
- **value:** `${email_result}`
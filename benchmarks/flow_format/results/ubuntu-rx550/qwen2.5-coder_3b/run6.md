# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `first_day`: `date.calc(date="${config.month.date}", add_months=-1, format="YYYY-MM-01")`
- `last_day`: `date.calc(date="${config.month.date}", add_months=-1, format="YYYY-MM-31")`
- `output_path`: "${config.output_path}"
- `currency_names`: "${config.currencies}"

## Steps

### 1. Initialize Browser (`web.open`)
- **url:** "${config.url}"
- **headless:** ${config.headless}
- **output_var:** `browser`
- **max_retries:** 2
- **Sub-steps:**
  - Accept Cookies (`ai.decide`):
    - **base_url:** "${config.url}"
    - **fallback_to_ollama:** true
    - **question:** "Accept recommended cookies"
    - **output_var:** `cookies_accepted`
    - **on_error:** continue

### 2. Navigate to Currency Filter (`web.get_attribute`)
- **selector:** "#dropdownCurrency"
- **attribute:** "textContent"
- **output_var:** `current_currency`
- **max_retries:** 2

### 3. Initialize Currency Selection (`logic.loop`)
- **items:** `${currency_names}`
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency Tab (`web.click`):
    - **selector:** "${currency}"
    - **output_var:** `currency_tab`
    - **on_error:** continue
    - **max_retries:** 2

### 4. Get Currency Table (`web.get_table`)
- **selector:** ".table tbody tr"
- **columns:** ["Period", "Buying Rates Transfer"]
- **output_var:** `currency_data`
- **max_retries:** 2

### 5. Append Currency Data (`logic.append`):
- **target:** `${currency_data}`
- **item:** {"Currency": "${currency}", ...}
- **extend:** true
- **max_retries:** 2

### 6. Write CSV (`csv.write`)
- **file_path:** "${output_path}"
- **data:** `${currency_data}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 7. Close Browser (`web.close`)
- **output_var:** `browser_closed`
- **max_retries:** 2

### 8. Email CSV (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** "${config.email.html}"
- **attachments:** "${output_path}"
- **smtp_host:** "${config.email.smtp_host}"
- **smtp_port:** "${config.email.smtp_port}"
- **smtp_user:** "${config.email.smtp_user}"
- **smtp_password:** "${config.email.smtp_password}"
- **use_tls:** ${config.email.use_tls}
- **dry_run:** ${config.email.dry_run}
- **on_error:** retry
- **max_retries:** 2
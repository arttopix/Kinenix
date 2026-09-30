# Bank of Thailand Exchange Rates Collector
> Description: Automate collecting historical foreign exchange rates (USD, GBP, SGD, JPY, EUR) for December 2024 from the Bank of Thailand (BOT) website, export to grouped Excel, and email to recipient.
> Version: 1.0.0

## Variables
- `exchange_rate_records`: []

## Steps

### 1. Open Bank of Thailand Exchange Rate Portal (`web.open`)
- **url:** `${config.bot_url}`
- **headless:** `${config.headless}`
- **timeout:** 30000
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 3.0

### 2. Check Cookie Consent Banner Visibility (`web.is_visible`)
- **selector:** `button:has-text('Accept recommended cookies'), button:has-text('Proceed with necessary cookies')`
- **timeout:** 2000
- **output_var:** `has_cookie_banner`
- **on_error:** continue

### 3. Decide Cookie Consent Action (`ai.decide`)
- **condition:** `${has_cookie_banner} == true`
- **state:** "ต้องการยินยอมรับคุกกี้เพื่อเปิดดูตารางอัตราแลกเปลี่ยนและให้เว็บไซต์ทำงานได้สมบูรณ์"
- **question:** {"name": "consent_button", "type": "choice", "instructions": "เลือกปุ่มที่เหมาะสมที่สุดในการกดยอมรับคุกกี้เพื่อเข้าใช้งานเว็บไซต์", "options": ["Accept recommended cookies", "Proceed with necessary cookies"]}
- **output_var:** `cookie_decision`
- **on_error:** continue

### 4. Click Cookie Consent Button (`web.click`)
- **condition:** `${has_cookie_banner} == true`
- **selector:** `button:has-text('${cookie_decision.choice}')`
- **timeout:** 3000
- **optional:** true
- **on_error:** continue

### 5. Wait for Portal Content and Table to Load (`web.wait_for`)
- **selector:** `div.table-responsive, table, select`
- **state:** visible
- **timeout:** 15000
- **on_error:** continue

### 6. Loop Through Target Currencies (`logic.loop`)
- **items:** `${config.currencies}`
- **item_var:** `currency`
- **Sub-steps:**
  - Select Target Currency from Dropdown (`web.select_option`):
    - **selector:** `select#currency, select[name*='currency'], select`
    - **text:** `${currency}`
    - **ai_match:** true
    - **on_error:** retry
    - **max_retries:** 2
  - Set Historical Start Date (`web.type`):
    - **selector:** `input#startDate, input[name*='startDate'], input[placeholder*='Start']`
    - **text:** `${config.start_date}`
  - Set Historical End Date (`web.type`):
    - **selector:** `input#endDate, input[name*='endDate'], input[placeholder*='End']`
    - **text:** `${config.end_date}`
  - Click Search or Apply Button (`web.click`):
    - **selector:** `button:has-text('Search'), button:has-text('Apply'), input[type='submit']`
  - Wait for Exchange Rate Table Update (`web.wait_for`):
    - **timeout:** 3000
  - Extract Transfer Rate Data from Table (`web.get_text`):
    - **selector:** `table tbody, div.table-responsive`
    - **output_var:** `raw_table_text`
  - Append Currency Transfer Rate Record (`logic.append`):
    - **target:** `exchange_rate_records`
    - **item:** `{"currency": "${currency}", "start_date": "${config.start_date}", "end_date": "${config.end_date}", "table_data": "${raw_table_text}"}`

### 7. Write Grouped Transfer Rates to Excel (`excel.write`)
- **file_path:** `${config.excel_output_path}`
- **data:** `${exchange_rate_records}`
- **on_error:** retry
- **max_retries:** 2

### 8. Capture Execution Proof Screenshot (`web.screenshot`)
- **path:** `${config.screenshot_path}`
- **full_page:** true
- **on_error:** continue

### 9. Close Browser Session (`web.close`)

### 10. Send Exchange Rates Report Email via Outlook/SMTP (`flow.call`)
- **condition:** `${config.send_email} == true`
- **flow:** `@shared/send_email.json`
- **inputs:** `{"to": "${config.email_recipient}", "subject": "${config.email_subject}", "body": "Hello,\n\nPlease find attached the Bank of Thailand Foreign Exchange Rates report (USD, GBP, SGD, JPY, EUR) for the period 01-12-2024 to 31-12-2024.\n\nBest regards,\nKinenix Worker", "attachments": ["${config.excel_output_path}"], "dry_run": "${config.dry_run}"}`
- **output_var:** `email_delivery_result`
- **on_error:** continue

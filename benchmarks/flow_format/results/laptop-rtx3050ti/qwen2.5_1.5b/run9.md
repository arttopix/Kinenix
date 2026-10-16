# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: {"url": "https://api.bankofthailand.com/transfer", "currencies": ["THB", "USD", "JPY", "EUR"], "month": {"date": "today", "add_months": -1}, "output_path": "/tmp/bank_rates.csv", "email": {"to": "example@example.com", "subject": "Bank of Thailand Buying Transfer Rates", "body": "Please find attached the monthly buying transfer rates."}, "dry_run": false}
- `name`: "collect_rates_flow"

## Steps

### 1. Open URL (`http.request`)
- **url:** "${config.url}"
- **method:** "GET"
- **headers:** {"cookie": "your_cookie_value"}
- **payload:** None
- **timeout:** 30

### 2. Accept Cookie Banner (`web.check`)
- **selector:** "button.text.Accept recommended cookies"
- **timeout:** 10

### 3. Open Currency Filter (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "Open Currency Filter"
- **timeout:** 10

### 4. Select Currencies (`web.select_option`)
- **selector:** ".currency-filter input[name='currencyCheck'][value='THB']"
- **value:** "THB"
- **label:** "Select THB"
- **timeout:** 10
- **retry_interval:** 5

### 5. Select Currencies (`web.select_option`)
- **selector:** ".currency-filter input[name='currencyCheck'][value='USD']"
- **value:** "USD"
- **label:** "Select USD"
- **timeout:** 10
- **retry_interval:** 5

### 6. Select Currencies (`web.select_option`)
- **selector:** ".currency-filter input[name='currencyCheck'][value='JPY']"
- **value:** "JPY"
- **label:** "Select JPY"
- **timeout:** 10
- **retry_interval:** 5

### 7. Select Currencies (`web.select_option`)
- **selector:** ".currency-filter input[name='currencyCheck'][value='EUR']"
- **value:** "EUR"
- **label:** "Select EUR"
- **timeout:** 10
- **retry_interval:** 5

### 8. Set Start Date (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "DD/MM/YYYY"
- **add_days:** 1
- **on_error:** retry
- **max_retries:** 2

### 9. Set End Date (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "DD/MM/YYYY"
- **add_days:** 1
- **on_error:** retry
- **max_retries:** 2

### 10. Select Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **value:** "${config.month.date}"
- **on_error:** retry
- **max_retries:** 2

### 11. Select Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${config.month.date}"
- **on_error:** retry
- **max_retries:** 2

### 12. Select Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${config.month.date}"
- **on_error:** retry
- **max_retries:** 2

### 13. Select Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${config.month.date}"
- **on_error:** retry
- **max_retries:** 2

### 14. Open Date Picker (`web.click`)
- **selector:** ".react-datepicker select"
- **label:** "Open Date Picker"
- **timeout:** 10

### 15. Click "button.historical-btn" (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Search"
- **timeout:** 10

### 16. Click Tab (`web.click`)
- **selector:** "text=THB"
- **label:** "Open tab"
- **timeout:** 10

### 17. Click Tab (`web.click`)
- **selector:** "text=USD"
- **label:** "Open tab"
- **timeout:** 10

### 18. Click Tab (`web.click`)
- **selector:** "text=JPY"
- **label:** "Open tab"
- **timeout:** 10

### 19. Click Tab (`web.click`)
- **selector:** "text=EUR"
- **label:** "Open tab"
- **timeout:** 10

### 20. Read Table (`web.get_table`)
- **selector:** ".react-datepicker select"
- **label:** "Read Table"
- **columns:** "Period" as "Date", "Buying Rates Transfer" as "Buying Transfer Rate"
- **numeric_columns:** ["Buying Transfer Rate"]
- **add_columns:** ["Currency"]
- **min_rows:** 5
- **timeout:** 10

### 21. Write to CSV (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** "${table}"
- **on_error:** retry
- **max_retries:** 2

### 22. Close Browser (`web.close`)
- **timeout:** 10

### 23. Email CSV (`email.send`)
- **to:** "${config.email.to}"
- **cc:** ""
- **bcc:** ""
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **html:** ""
- **attachments:** "${config.output_path}"
- **smtp_host:** "smtp.gmail.com"
- **smtp_port:** 587
- **smtp_user:** "your_email@gmail.com"
- **smtp_password:** "your_password"
- **use_tls:** true
- **dry_run:** "${config.dry_run}"
- **on_error:** retry
- **max_retries:** 2

### 24. Set Dry Run (`logic.set_variable`)
- **name:** "dry_run"
- **value:** "${config.dry_run}"

### 25. Send Email (`email.send`)
- **to:** "${config.email.to}"
- **cc:** ""
- **bcc:** ""
- **subject:** "${config.email.subject}"
- **body:** ""
- **html:** ""
- **attachments:** ""
- **smtp_host:** "smtp.gmail.com"
- **smtp_port:** 587
- **smtp_user:** "your_email@gmail.com"
- **smtp_password:** "your_password"
- **use_tls:** true
- **dry_run:** "${config.dry_run}"
- **on_error:** retry
- **max_retries:** 2

### 26. Wait for Dry Run (`logic.delay`)
- **seconds:** 10

### 27. Set Dry Run (`logic.set_variable`)
- **name:** "dry_run"
- **value:** "false"

### 28. Wait for Dry Run (`logic.delay`)
- **seconds:** 10

### 29. Set Dry Run (`logic.set_variable`)
- **name:** "dry_run"
- **value:** "false"
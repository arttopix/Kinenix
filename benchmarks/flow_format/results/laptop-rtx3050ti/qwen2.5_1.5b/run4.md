# Collect Bank of Thailand Buying Transfer Rates for Several Currencies

## Variables
- `config.url`: "https://www.btc.th"
- `config.currencies`: ["THB", "USD", "EUR", "JPY", "THB", "USD", "EUR", "JPY"]
- `config.month.date`: "today"
- `config.month.add_months`: -1
- `config.output_path`: "output/bank_rates.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates"
- `config.email.body`: "Dear [Recipient],\n\nPlease find attached the Bank of Thailand buying transfer rates for the next month.\n\nBest regards,\n[Your Name]"
- `config.email.dry_run`: false

## Steps

### 1. Get Report Month (`logic.set_variable`)
- **name:** `report_month`
- **value:** `config.month.date`

### 2. Open URL and Accept Cookies (`http.request`)
- **url:** `config.url`
- **method:** "GET"
- **headers:** {"Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh-HK;q=0.6,zh-TW-Ext;q=0.5"}
- **payload:** {}
- **timeout:** 30

### 3. Filter Currency Dropdown (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **value:** "currencyCheck"
- **text:** "currency"
- **base_url:** "https://www.btc.th"
- **systemone_url:** "https://www.btc.th"
- **fallback_to_ollama:** false

### 4. Select Start and End Dates (`web.select_option`)
- **selector:** "#react-datepicker-calendar > div"
- **input_format:** "%Y-%m-%d"
- **min_rows:** 5
- **timeout:** 30

### 5. Search for Rates (`web.select_option`)
- **selector:** "#historicalBtn"
- **base_url:** "https://www.btc.th"
- **systemone_url:** "https://www.btc.th"
- **fallback_to_ollama:** false
- **timeout:** 30

### 6. Write Rates to CSV (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `${config.currencies}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **append:** true

### 7. Close Browser and Send Email (`email.send`)
- **to:** `${config.email.to}`
- **cc:** []
- **bcc:** []
- **subject:** `${config.email.subject}`
- **body:** `${config.email.body}`
- **html:** false
- **attachments:** []
- **smtp_host:** "smtp.gmail.com"
- **smtp_port:** 587
- **smtp_user:** "your-email@gmail.com"
- **smtp_password:** "your-email-password"
- **use_tls:** true
- **dry_run:** false
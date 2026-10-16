# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `config`: {}
- `output_path`: ./results/boths_transfer_rates.csv
- `email.to`: example@example.com
- `email.subject`: "Bank of Thailand Buying Transfer Rates Report"
- `email.body`: "This is the body of the email."
- `email.dry_run`: false

## Steps

### 1. Initialize Variables
- **output_var:** `config.output_path`

### 2. Determine the Month and Last Day
- **config.month:** {"date": "today", "add_months": -1}

### 3. Open the URL and Accept Cookies
- **http.request:** "https://www.btc.th/", "GET", {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9", "Accept-Language": "en-US,en;q=0.9", "Origin": "https://www.btc.th", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "Referer": "https://www.btc.th/", "Sec-Fetch-Script": "empty", "Sec-Fetch-User": "?1", "Sec-GPC": "true", "Cookie": ""}

### 4. Add the Currencies
- **config.currencies:** ["THB", "USD", "EUR", "JPY", "CNY", "AUD", "NZD"]

### 5. Open the Currency Filter and Select Currencies
- **web.click:** "//*[@id='dropdownCurrency']", "Accept recommended cookies"

### 6. Select Start and End Dates
- **date.calc:** "year select", "input_format", "%Y-%m-%d", "day cell text", "${config.month.date} ${config.month.add_months}"
- **web.click:** "//*[@id='react-datepicker-range--startDate']/div/ul/li[1]", "day cell text", "2023-01-01"
- **web.click:** "//*[@id='react-datepicker-range--endDate']/div/ul/li[2]", "day cell text", "2023-01-31"

### 7. Search for Historical Rates
- **web.click:** "button.historical-btn"

### 8. Read the CSV and Write to Output Path
- **http.request:** "https://www.btc.th/", "GET", {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Accept-Language": "en-US,en;q=0.9", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9", "Origin": "https://www.btc.th", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36", "Referer": "https://www.btc.th/", "Sec-Fetch-Script": "empty", "Sec-Fetch-User": "?1", "Sec-GPC": "true", "Cookie": ""}
- **http.download:** "https://www.btc.th/", "target_path", "output.csv"
- **csv.read:** "output.csv", "delimiter", ";", "encoding", "ISO-8859-1", "clean_headers", "true", "append", "false", "on_error", "retry", "max_retries", "2", "retry_interval", "10"
- **csv.write:** "${output_path}", "data", "header", "ISO-8859-1", "append", "false", "on_error", "retry", "max_retries", "2", "retry_interval", "10"

### 9. Close the Browser and Email the CSV
- **web.close:** (none)
- **email.send:** "${email.to}", "${email.cc}", "${email.bcc}", "${email.subject}", "${email.body}", "${email.html}", "${email.attachments}", "${email.smtp_host}", "${email.smtp_port}", "${email.smtp_user}", "${email.smtp_password}", "${email.use_tls}", "${email.dry_run}"

### 10. Log the Output Path
- **output_var:** `config.output_path`

### 11. Retry Handling
- **config.max_retries:** 2
- **config.retry_interval:** 10

### 12. Error Handling
- **config.on_error:** retry
# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `base_url`: ""
- `url`: ""
- `currencies`: ""
- `month.date`: ""
- `month.add_months`: -1
- `config.month`: {"date": "today", "add_months": -1}
- `config.output_path`: ""
- `config.email.to`: ""
- `config.email.subject`: ""
- `config.email.body`: ""
- `config.email.dry_run`: false
- `headless`: false
- `config.currencies`: []
- `config.url`: ""
- `config.output_path`: ""
- `config.email.to`: ""
- `config.email.subject`: ""
- `config.email.body`: ""
- `config.email.dry_run`: false
- `output_path`: ""
- `email.to`: ""
- `email.subject`: ""
- `email.body`: ""
- `email.dry_run`: false

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** "${config.month.add_months}"
- **output_var:** `first_day_last_month`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **get_first_day_last_month:** `date.calc("${config.month.date}", "%Y-%m-01", "%Y-%m-01", "%Y-%m-01", "${config.month.add_months}", "%Y-%m-01", "%Y-%m-01")`
  - **get_last_day_last_month:** `date.calc("${config.month.date}", "%Y-%m-%d", "%Y-%m-%d", "%Y-%m-%d", "${config.month.add_months}", "%Y-%m-%d", "%Y-%m-%d")`

### 2. Open ${config.url}; accept the cookie banner if it appears (`web.click`)
- **selector:** ".react-cookie-consent button:contains('Accept recommended cookies')"
- **label:** "Accept recommended cookies"
- **output_var:** `accept_cookies_button`
- **on_error:** continue
- **max_retries:** 1

### 3. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "dropdownCurrency"
- **output_var:** `currency_filter`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **open_currency_filter:** `web.click("${currency_filter}", "${currency_filter}")`
  - **tick_each_currency:** `logic.loop("${config.currencies}")`
    - **item_var:** `currency`
    - **Sub-steps:**
      - **click_currency:** `web.click("${currency_filter} .currency-filter input[name='currencyCheck'][value='${currency}']", "${currency} .currency-filter input[name='currencyCheck'][value='${currency}']")`

### 4. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.click`)
- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **output_var:** `month_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_month:** `web.select_option("${month_selector}", "${month_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}")`
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **output_var:** `year_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_year:** `web.select_option("${year_selector}", "${year_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}"`)

### 5. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **output_var:** `search_button`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **click_search_button:** `web.click("${search_button}", "${search_button}")`

### 6. For each currency, click its tab button (text = currency) and read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (a number), add a Currency column (`web.click`)
- **selector:** ".react-datepicker table"
- **label:** "react-datepicker table"
- **output_var:** `table`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **read_table:** `web.get_table("${table}", "${table}", ["Period", "Buying Rates Transfer"], ["Period", "Buying Rates Transfer"], ["Currency"], 10, 5)`

### 7. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 1
- **Sub-steps:**
  - **write_rows:** `csv.write("${output_path}", "${rows}", ["Currency", "Date", "Buying Transfer Rate"])`

### 8. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}) (`web.click`)
- **selector:** "button.close"
- **label:** "close"
- **output_var:** `close_button`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **click_close_button:** `web.click("${close_button}", "${close_button}")`
- **email:** `email.send("${email.to}", "${email.to}", "${email.subject}", "${email.body}", "${output_path}", "${email.smtp_host}", "${email.smtp_port}", "${email.smtp_user}", "${email.smtp_password}", "${email.use_tls}", "${email.dry_run}")`

### 9. Screenshot (`web.screenshot`)
- **path:** "./report.png"
- **full_page:** true

### 10. Open ${config.url}; accept the cookie banner if it appears (`web.click`)
- **selector:** ".react-cookie-consent button:contains('Accept recommended cookies')"
- **label:** "Accept recommended cookies"
- **output_var:** `accept_cookies_button`
- **on_error:** continue
- **max_retries:** 1

### 11. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "dropdownCurrency"
- **output_var:** `currency_filter`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **open_currency_filter:** `web.click("${currency_filter}", "${currency_filter}")`
  - **tick_each_currency:** `logic.loop("${config.currencies}")`
    - **item_var:** `currency`
    - **Sub-steps:**
      - **click_currency:** `web.click("${currency_filter} .currency-filter input[name='currencyCheck'][value='${currency}']", "${currency} .currency-filter input[name='currencyCheck'][value='${currency}']")`

### 12. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.click`)
- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **output_var:** `month_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_month:** `web.select_option("${month_selector}", "${month_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}")`
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **output_var:** `year_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_year:** `web.select_option("${year_selector}", "${year_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}")`

### 13. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **output_var:** `search_button`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **click_search_button:** `web.click("${search_button}", "${search_button}")`

### 14. For each currency, click its tab button (text = currency) and read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (a number), add a Currency column (`web.click`)
- **selector:** ".react-datepicker table"
- **label:** "react-datepicker table"
- **output_var:** `table`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **read_table:** `web.get_table("${table}", "${table}", ["Period", "Buying Rates Transfer"], ["Period", "Buying Rates Transfer"], ["Currency"], 10, 5)`

### 15. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 1
- **Sub-steps:**
  - **write_rows:** `csv.write("${output_path}", "${rows}", ["Currency", "Date", "Buying Transfer Rate"])`

### 16. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}) (`web.click`)
- **selector:** "button.close"
- **label:** "close"
- **output_var:** `close_button`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **click_close_button:** `web.click("${close_button}", "${close_button}")`
- **email:** `email.send("${email.to}", "${email.to}", "${email.subject}", "${email.body}", "${output_path}", "${email.smtp_host}", "${email.smtp_port}", "${email.smtp_user}", "${email.smtp_password}", "${email.use_tls}", "${email.dry_run}")`

### 17. Screenshot (`web.screenshot`)
- **path:** "./report.png"
- **full_page:** true

### 18. Open ${config.url}; accept the cookie banner if it appears (`web.click`)
- **selector:** ".react-cookie-consent button:contains('Accept recommended cookies')"
- **label:** "Accept recommended cookies"
- **output_var:** `accept_cookies_button`
- **on_error:** continue
- **max_retries:** 1

### 19. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "dropdownCurrency"
- **output_var:** `currency_filter`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **open_currency_filter:** `web.click("${currency_filter}", "${currency_filter}")`
  - **tick_each_currency:** `logic.loop("${config.currencies}")`
    - **item_var:** `currency`
    - **Sub-steps:**
      - **click_currency:** `web.click("${currency_filter} .currency-filter input[name='currencyCheck'][value='${currency}']", "${currency} .currency-filter input[name='currencyCheck'][value='${currency}']")`

### 20. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.click`)
- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **output_var:** `month_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_month:** `web.select_option("${month_selector}", "${month_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}")`
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **output_var:** `year_selector`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **select_year:** `web.select_option("${year_selector}", "${year_selector}", "${first_day_last_month.split('-')[0]}", "${first_day_last_month.split('-')[1]}")`

### 21. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **output_var:** `search_button`
- **on_error:** continue
- **max_retries:** 1
- **Sub-steps:**
  - **click_search_button:** `web.click("${search_button}", "${search
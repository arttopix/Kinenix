# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `url`: <https://www.bangkokbank.com>
- `currencies`: ["THB", "USD", "EUR", "JPY"]
- `month.date`: "2023-10-01"
- `month.add_months`: -1
- `output_path`: "./output/bank-of-thailand.csv"
- `headless`: "true"
- `email.to`: "example@example.com"
- `email.subject`: "Bank of Thailand Buying Transfer Rates for ${month.date}"
- `email.body`: "Please find the following Buying Transfer Rates for Bank of Thailand."
- `email.dry_run`: "false"

## Steps

### 1. Work out the first and last day of the report month (`date.calc`)
- **date:** "${config.month.date}"
- **input_format:** "%Y-%m-%d"
- **add_months:** ${config.month.add_months}
- **output_var:** `month_range`
- **on_error:** retry
- **max_retries:** 2

### 2. Open ${config.url}; accept the cookie banner if it appears (`web.check`)
- **selector:** "button[aria-label='Accept recommended cookies']"
- **label:** "Accept recommended cookies"
- **output_var:** `accept_banner`
- **on_error:** retry
- **max_retries:** 2

### 3. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies} (`web.select_option`)
- **selector:** "#dropdownCurrency"
- **label:** "Select Currency"
- **value:** "${item}"
- **text:** "Select Currency"
- **index:** "${item}"
- **items:** "${config.currencies}"
- **item_var:** `currency`
- **Sub-steps:**
  - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
  - **label:** "Currency"
  - **action:** "web.select_option"
  - **item_var:** `currency`

### 4. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1', month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **value:** "${month_range[0]}"
- **text:** "2023"
- **index:** "0"
- **items:** ["${month_range[0]}", "${month_range[1]}"]
- **item_var:** `year`

- **selector:** ".react-datepicker select >> nth=0"
- **label:** "Month"
- **value:** "${month_range[0]}"
- **text:** "October"
- **index:** "0"
- **items:** ["${month_range[0]}", "${month_range[1]}"]
- **item_var:** `month`

- **selector:** ".react-datepicker input"
- **label:** "Day"
- **value:** "${month_range[0]}"
- **text:** "${month_range[0]}"
- **index:** "0"
- **items:** ["${month_range[0]}", "${month_range[1]}"]
- **item_var:** `day`

### 5. Click 'button.historical-btn' to search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "Historical"
- **output_var:** `search_result`

### 6. For each currency, click its tab button (text = currency) and read the visible table: keep columns "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (`web.select_option`)
- **selector:** "#currencyTabs"
- **label:** "Currency Tabs"
- **value:** "${currency}"
- **text:** "${currency}"
- **index:** "${currency}"
- **items:** "${currencies}"
- **item_var:** `currency`

- **selector:** ".react-datepicker input"
- **label:** "Day"
- **value:** "${day}"
- **text:** "${day}"
- **index:** "${day}"
- **items:** ["${day}", "${day + 1}"]
- **item_var:** `day`

- **selector:** "table"
- **label:** "Table"
- **action:** "web.get_table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** []
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **items:** "${currencies}"
- **item_var:** `currency`

- **selector:** "table"
- **label:** "Table"
- **action:** "web.get_table"
- **columns:** ["Period", "Buying Rates Transfer"]
- **numeric_columns:** []
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **items:** "${currencies}"
- **item_var:** `currency`

### 7. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate (`csv.write`)
- **file_path:** "${config.output_path}"
- **data:** `${rows}`
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **encoding:** "utf-8"
- **on_error:** retry
- **max_retries:** 2

### 8. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}) (`email.send`)
- **to:** "${config.email.to}"
- **subject:** "${config.email.subject}"
- **body:** "${config.email.body}"
- **attachments:** "${config.output_path}"
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** "true"
- **dry_run:** "${config.email.dry_run}"
- **output_var:** `email_result`
- **on_error:** retry
- **max_retries:** 2
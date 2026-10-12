# Collect Bank of Thailand Transfer Rates

## Variables
- `base_url`: "${config.url}"
- `currencies`: "${config.currencies}"
- `month_date`: "${config.month.date}"
- `month_add_months`: "${config.month.add_months}"
- `output_path`: "${config.output_path}"
- `email_to`: "${config.email.to}"
- `email_subject`: "${config.email.subject}"
- `email_body`: "${config.email.body}"
- `email_dry_run`: "${config.email.dry_run}"
- `config`: "${config}"
- `headless`: "${config.headless}"
- `session`: "${session}"
- `timeout`: 10

## Steps

### 1. Work Out Month (`date.calc`)
- **date:** "${month_date.date}"
- **add_months:** "${month_add_months}"
- **format:** "%Y-%m-%d"
- **output_var:** `month_start_date`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Convert Month (`date.calc`):
    - **date:** "${month_start_date}"
    - **add_months:** 1
    - **format:** "%Y-%m-01"
    - **output_var:** `month_end_date`
    - **on_error:** retry
    - **max_retries:** 2

### 2. Open Browser (`web.open`)
- **url:** "${base_url}"
- **headless:** "${headless}"
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 3. Accept Cookie Banner (`web.click`)
- **selector:** "button:contains('Accept recommended cookies')"
- **label:** "Accept recommended cookies"
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 4. Open Currency Filter (`web.click`)
- **selector:** "#dropdownCurrency"
- **label:** "Open dropdown"
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2

### 5. Tick Currencies (`logic.loop`)
- **items:** "${currencies}"
- **item_var:** `currency`
- **Sub-steps:**
  - Click Currency (`web.click`):
    - **selector:** ".currency-filter input[name='currencyCheck'][value='${currency}']"
    - **label:** "${currency}"
    - **timeout:** "${timeout}"
    - **output_var:** `browser`
    - **on_error:** retry
    - **max_retries:** 2

### 6. Pick Start and End Dates (`web.select_option` and `web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **value:** "${month_start_date.year}"
- **text:** "${month_start_date.year}"
- **label_text:** "${month_start_date.year}"
- **index:** 1
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
    - **Sub-steps:**
      - **selector:** ".react-datepicker select >> nth=0"
      - **label:** "Month"
      - **value:** "${month_start_date.month}"
      - **text:** "${month_start_date.month}"
      - **label_text:** "${month_start_date.month}"
      - **index:** 0
      - **timeout:** "${timeout}"
      - **output_var:** `browser`
      - **on_error:** retry
      - **max_retries:** 2
      - **Sub-steps:**
        - **selector:** ".react-datepicker select >> nth=0"
        - **label:** "Day"
        - **value:** "${month_start_date.day}"
        - **text:** "${month_start_date.day}"
        - **label_text:** "${month_start_date.day}"
        - **index:** 0
        - **timeout:** "${timeout}"
        - **output_var:** `browser`
        - **on_error:** retry
        - **max_retries:** 2

### 7. Pick End Dates (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=1"
- **label:** "Year"
- **value:** "${month_end_date.year}"
- **text:** "${month_end_date.year}"
- **label_text:** "${month_end_date.year}"
- **index:** 1
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
    - **Sub-steps:**
      - **selector:** ".react-datepicker select >> nth=0"
      - **label:** "Month"
      - **value:** "${month_end_date.month}"
      - **text:** "${month_end_date.month}"
      - **label_text:** "${month_end_date.month}"
      - **index:** 0
      - **timeout:** "${timeout}"
      - **output_var:** `browser`
      - **on_error:** retry
      - **max_retries:** 2
      - **Sub-steps:**
        - **selector:** ".react-datepicker select >> nth=0"
        - **label:** "Day"
        - **value:** "${month_end_date.day}"
        - **text:** "${month_end_date.day}"
        - **label_text:** "${month_end_date.day}"
        - **index:** 0
        - **timeout:** "${timeout}"
        - **output_var:** `browser`
        - **on_error:** retry
        - **max_retries:** 2

### 8. Search (`web.click`)
- **selector:** "button.historical-btn"
- **label:** "button.historical-btn"
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
    - **Sub-steps:**
      - **selector:** ".currency-filter"
      - **label:** "button.currency-filter"
      - **timeout:** "${timeout}"
      - **output_var:** `browser`
      - **on_error:** retry
      - **max_retries:** 2

### 9. Read and Save Data (`web.get_table`, `csv.write`, `logic.loop`, `csv.write`)
- **selector:** ".currency-table"
- **label:** "table.currency-table"
- **columns:** ["Date", "Buying Rates Transfer"]
- **numeric_columns:** ["Buying Rates Transfer"]
- **add_columns:** ["Currency"]
- **min_rows:** 1
- **timeout:** "${timeout}"
- **output_var:** `browser`
- **on_error:** retry
    - **Sub-steps:**
      - **selector:** ".currency-table"
      - **label:** "table.currency-table"
      - **timeout:** "${timeout}"
      - **output_var:** `browser`
      - **on_error:** retry
      - **max_retries:** 2
      - **Sub-steps:**
        - **data:** `${browser}`
        - **columns:** ["Date", "Buying Rates Transfer"]
        - **encoding:** "utf-8"
        - **append:** False
        - **output_var:** `data`
        - **on_error:** retry
        - **max_retries:** 2

### 10. Collect Data for Each Currency (`logic.loop`)
- **items:** "${currencies}"
- **item_var:** `currency`
- **Sub-steps:**
  - **data:** `${data}`
  - **columns:** ["Currency", "Date", "Buying Rates Transfer"]
  - **encoding:** "utf-8"
  - **append:** False
  - **output_var:** `data`
  - **on_error:** retry
    - **Sub-steps:**
      - **data:** `${data}`
      - **columns:** ["Currency", "Date", "Buying Rates Transfer"]
      - **encoding:** "utf-8"
      - **append:** True
      - **output_var:** `data`
      - **on_error:** retry
      - **max_retries:** 2

### 11. Write Output CSV (`csv.write`)
- **file_path:** "${output_path}"
- **data:** `${data}`
- **columns:** ["Currency", "Date", "Buying Rates Transfer"]
- **encoding:** "utf-8"
- **append:** False
- **output_var:** `data`
- **on_error:** retry
    - **Sub-steps:**
      - **data:** `${data}`
      - **columns:** ["Currency", "Date", "Buying Rates Transfer"]
      - **encoding:** "utf-8"
      - **append:** True
      - **output_var:** `data`
      - **on_error:** retry
      - **max_retries:** 2

### 12. Close Browser (`web.close`)
- **output_var:** `browser`
- **on_error:** retry
    - **Sub-steps:**
      - **browser:** `${browser}`
      - **output_var:** `browser`
      - **on_error:** retry
      - **max_retries:** 2

### 13. Email CSV (`email.send`)
- **to:** "${email_to}"
- **subject:** "${email_subject}"
- **body:** "${email_body}"
- **html:** False
- **attachments:** [`${output_path}`]
- **smtp_host:** "smtp.example.com"
- **smtp_port:** 587
- **smtp_user:** "user@example.com"
- **smtp_password:** "password"
- **use_tls:** True
- **dry_run:** "${email_dry_run}"
- **output_var:** `email_result`
- **on_error:** retry
    - **Sub-steps:**
      - **email_result:** `${email_result}`
      - **output_var:** `email_result`
      - **on_error:** retry
      - **max_retries:** 2
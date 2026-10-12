# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `first_day`: $(date.calc {"date": "${config.month.date}", "add_months": -1})
- `last_day`: $(date.calc {"date": "${config.month.date}", "add_months": 0})
- `report_date`: $(date.format {"date": "${first_day}", "format": "yyyy-MM-dd"})
- `last_month`: $(date.format {"date": "${first_day}", "format": "yyyy-MM"})
- `today`: $(date.format {"date": "today", "format": "yyyy-MM-dd"})
- `output_path`: ${config.output_path}
- `email_to`: ${config.email.to}
- `email_subject`: Bank of Thailand Buying Transfer Rates - ${report_date}
- `email_body`: Please find the attached CSV file containing Bank of Thailand buying transfer rates for ${report_date}.
- `config`: ${config}

## Steps

### 1. Initialize and Open URL (`web.open`)
- **url:** ${config.url}
- **description:** Initialize and open the Bank of Thailand website.
- **output_var:** `browser`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**
  - Click Cookie Banner (`web.click`):
    - **selector:** button.historical-btn
    - **description:** Click the cookie banner if it appears.
    - **on_error:** retry
    - **max_retries:** 2

### 2. Set Date Range (`date.calc`)
- **date:** "${first_day}"
- **description:** Set the start date for the report.
- **output_var:** `start_date`
- **on_error:** retry
- **max_retries:** 2

### 3. Set Date Range (`date.calc`)
- **date:** "${last_day}"
- **description:** Set the end date for the report.
- **output_var:** `end_date`
- **on_error:** retry
- **max_retries:** 2

### 4. Open Currency Filter (`web.select_option`)
- **selector:** #dropdownCurrency
- **description:** Open the currency filter dropdown.
- **output_var:** `currency_filter`
- **on_error:** retry
- **max_retries:** 2

### 5. Select Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** `currency`
- **Sub-steps:**
  - Check Currency (`web.select_option`):
    - **selector:** .currency-filter input[name='currencyCheck'][value='${currency}']
    - **description:** Check the currency in the filter.
    - **on_error:** retry
    - **max_retries:** 2

### 6. Select Date Range (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=1'
- **description:** Select the year for the date range.
- **output_var:** `year_select`
- **on_error:** retry
- **max_retries:** 2

### 7. Select Date Range (`web.select_option`)
- **selector:** '.react-datepicker select >> nth=0'
- **description:** Select the month for the date range.
- **output_var:** `month_select`
- **on_error:** retry
- **max_retries:** 2

### 8. Set Start Date (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${start_date}"
- **description:** Set the start date in the date picker.
- **on_error:** retry
- **max_retries:** 2

### 9. Set End Date (`web.select_option`)
- **selector:** ".react-datepicker select >> nth=0"
- **value:** "${end_date}"
- **description:** Set the end date in the date picker.
- **on_error:** retry
- **max_retries:** 2

### 10. Search for Rates (`web.click`):
- **selector:** button.historical-btn
- **description:** Click the search button to retrieve rates.
- **on_error:** retry
- **max_retries:** 2

### 11. Get Currency Tabs (`web.get_table`)
- **selector:** ".currency-card"
- **description:** Retrieve the currency tabs.
- **output_var:** `currency_tabs`
- **on_error:** retry
- **max_retries:** 2

### 12. Get Rates for Each Currency (`logic.loop`)
- **items:** ${currency_tabs}
- **item_var:** `currency_tab`
- **Sub-steps:**
  - Click Currency Tab (`web.click`):
    - **selector:** text = ${currency_tab}
    - **description:** Click the tab for the currency.
    - **on_error:** retry
    - **max_retries:** 2

  - Get Rates (`web.get_table`):
    - **selector:** "table.table-sm"
    - **description:** Retrieve the rates table.
    - **output_var:** `rates_table`
    - **on_error:** retry
    - **max_retries:** 2

  - Extract Rates (`logic.loop`):
    - **items:** "${rates_table.rows}"
    - **item_var:** `rate`
    - **Sub-steps:**
      - Get Date (`web.get_text`):
        - **selector:** "td:nth-child(1)"
        - **description:** Extract the date.
        - **output_var:** `date`
        - **on_error:** retry
        - **max_retries:** 2

      - Get Buying Transfer Rate (`web.get_text`):
        - **selector:** "td:nth-child(2)"
        - **description:** Extract the buying transfer rate.
        - **output_var:** `buying_rate`
        - **on_error:** retry
        - **max_retries:** 2

      - Append Row (`logic.append`):
        - **target:** rates
        - **item:** {"Currency": "${currency}", "Date": "${date}", "Buying Transfer Rate": "${buying_rate}"}

### 13. Write Rates to CSV (`csv.write`)
- **file_path:** ${output_path}
- **data:** "${rates}"
- **columns:** ["Currency", "Date", "Buying Transfer Rate"]
- **on_error:** retry
- **max_retries:** 2

### 14. Close Browser (`web.close`)
- **description:** Close the browser.
- **on_error:** continue
- **max_retries:** 1

### 15. Send Email (`email.send`)
- **to:** ${email_to}
- **subject:** ${email_subject}
- **body:** ${email_body}
- **html:** (none)
- **attachments:** ${output_path}
- **on_error:** retry
- **max_retries:** 2

### 16. Cleanup (`file.delete`)
- **path:** ${output_path}
- **description:** Delete the CSV file.
- **on_error:** retry
- **max_retries:** 2

### 17. End (`flow.fail`)
- **message:** (none)
- **category:** (none)

---

This flow collects Bank of Thailand buying transfer rates for several currencies over one month, writes them to a CSV file, and sends the file as an email. It handles errors and retries where necessary.
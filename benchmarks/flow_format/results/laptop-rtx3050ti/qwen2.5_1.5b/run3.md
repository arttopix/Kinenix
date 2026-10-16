# Collect Bank of Thailand Buying Transfer Rates and Email as CSV

## Variables
- `config.url`: ""
- `config.currencies`: ["THB", "EUR", "JPY", "USD"]
- `config.month.date`: "today"
- `config.month.add_months`: -1
- `config.output_path`: "buying_transfer_rates.csv"
- `config.email.to`: "example@example.com"
- `config.email.subject`: "Bank of Thailand Buying Transfer Rates Report"
- `config.email.body`: "Dear [Recipient],\n\nAttached is your monthly report on Bank of Thailand buying transfer rates for the currencies specified.\n\nBest regards,\n[Your Name]"
- `config.headless`: false
- `config.email.dry_run`: false

## Steps

### 1. Define URL and Set Headless Mode
- **base_url:** "https://api.bankofthailand.com"
- **fallback_to_ollama:** false
- **question:** "Please open the Bank of Thailand website and navigate to the page you want to scrape."
- **state:** "Collect URL"
- **timeout:** 60

### 2. Open URL and Accept Cookie Banner
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "open_page.png"
- **instructions:** "Click 'Accept recommended cookies' to proceed."
- **model:** "gpt-3.5-turbo"
- **schema:** "open_page.png"
- **text:** "Please open the Bank of Thailand website and navigate to the page you want to scrape."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 3. Open Currency Filter and Select Currencies
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "currency_filter.png"
- **instructions:** "Click 'Dropdown Currency' and select the currencies you want to include."
- **model:** "gpt-3.5-turbo"
- **schema:** "currency_filter.png"
- **text:** "Click 'Dropdown Currency' and select the currencies you want to include."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `currency_filter`
- **Sub-steps:**

  ### 3.1. Select Currency Tab
  - **base_url:** "https://api.bankofthailand.com"
  - **image_path:** "select_currency.png"
  - **instructions:** "Click on the tab corresponding to the selected currency to filter the data."
  - **model:** "gpt-3.5-turbo"
  - **schema:** "select_currency.png"
  - **text:** "Click on the tab corresponding to the selected currency to filter the data."
  - **timeout:** 60
  - **on_error:** retry
  - **max_retries:** 2
  - **retry_interval:** 5

### 4. Open Date Picker and Set Start and End Dates
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "date_picker.png"
- **instructions:** "Set the start and end dates for the report."
- **model:** "gpt-3.5-turbo"
- **schema:** "date_picker.png"
- **text:** "Set the start and end dates for the report."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `date_picker`
- **Sub-steps:**

  ### 4.1. Set Start Date
  - **base_url:** "https://api.bankofthailand.com"
  - **image_path:** "set_start_date.png"
  - **instructions:** "Set the start date for the report."
  - **model:** "gpt-3.5-turbo"
  - **schema:** "set_start_date.png"
  - **text:** "Set the start date for the report."
  - **timeout:** 60
  - **on_error:** retry
  - **max_retries:** 2
  - **retry_interval:** 5
  - **output_var:** `start_date`
  - **Sub-steps:**

    ### 4.2. Set End Date
    - **base_url:** "https://api.bankofthailand.com"
    - **image_path:** "set_end_date.png"
    - **instructions:** "Set the end date for the report."
    - **model:** "gpt-3.5-turbo"
    - **schema:** "set_end_date.png"
    - **text:** "Set the end date for the report."
    - **timeout:** 60
    - **on_error:** retry
    - **max_retries:** 2
    - **retry_interval:** 5
    - **output_var:** `end_date`

### 5. Click 'Search' Button
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "search_button.png"
- **instructions:** "Click the search button to fetch the data."
- **model:** "gpt-3.5-turbo"
- **schema:** "search_button.png"
- **text:** "Click the search button to fetch the data."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `search_button`
- **Sub-steps:**

  ### 5.1. Click Search Button
  - **base_url:** "https://api.bankofthailand.com"
  - **image_path:** "click_search_button.png"
  - **instructions:** "Click the search button to fetch the data."
  - **model:** "gpt-3.5-turbo"
  - **schema:** "click_search_button.png"
  - **text:** "Click the search button to fetch the data."
  - **timeout:** 60
  - **on_error:** retry
  - **max_retries:** 2
  - **retry_interval:** 5

### 6. Read Data from Table
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "table_data.png"
- **instructions:** "Select the table and read the data."
- **model:** "gpt-3.5-turbo"
- **schema:** "table_data.png"
- **text:** "Select the table and read the data."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `data`

### 7. Prepare CSV Headers
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "csv_headers.png"
- **instructions:** "Prepare the CSV headers."
- **model:** "gpt-3.5-turbo"
- **schema:** "csv_headers.png"
- **text:** "Prepare the CSV headers."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `csv_headers`

### 8. Write Data to CSV
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "csv_write.png"
- **instructions:** "Write the data to a CSV file."
- **model:** "gpt-3.5-turbo"
- **schema:** "csv_write.png"
- **text:** "Write the data to a CSV file."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `csv_data`

### 9. Save CSV to Output Path
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "save_csv.png"
- **instructions:** "Save the CSV file to the output path."
- **model:** "gpt-3.5-turbo"
- **schema:** "save_csv.png"
- **text:** "Save the CSV file to the output path."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `save_csv`

### 10. Email CSV File
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "email_csv.png"
- **instructions:** "Email the CSV file to the specified email address."
- **model:** "gpt-3.5-turbo"
- **schema:** "email_csv.png"
- **text:** "Email the CSV file to the specified email address."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `email_csv`

### 11. Close Browser
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "close_browser.png"
- **instructions:** "Close the browser."
- **model:** "gpt-3.5-turbo"
- **schema:** "close_browser.png"
- **text:** "Close the browser."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5

### 12. Finalize and Send Email
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "finalize_email.png"
- **instructions:** "Finalize and send the email."
- **model:** "gpt-3.5-turbo"
- **schema:** "finalize_email.png"
- **text:** "Finalize and send the email."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `finalize_email`

### 13. Email Dry Run
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "dry_run_email.png"
- **instructions:** "Perform a dry run to test the email sending."
- **model:** "gpt-3.5-turbo"
- **schema:** "dry_run_email.png"
- **text:** "Perform a dry run to test the email sending."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `dry_run_email`

### 14. Email with SMTP
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "email_with_smtp.png"
- **instructions:** "Send the email using SMTP settings."
- **model:** "gpt-3.5-turbo"
- **schema:** "email_with_smtp.png"
- **text:** "Send the email using SMTP settings."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `email_smtp`

### 15. Dry Run Email without SMTP
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "dry_run_email_without_smtp.png"
- **instructions:** "Perform a dry run without SMTP to test the email sending."
- **model:** "gpt-3.5-turbo"
- **schema:** "dry_run_email_without_smtp.png"
- **text:** "Perform a dry run without SMTP to test the email sending."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `dry_run_email_without_smtp`

### 16. Finalize Email without SMTP
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "finalize_email_without_smtp.png"
- **instructions:** "Finalize the email without SMTP settings."
- **model:** "gpt-3.5-turbo"
- **schema:** "finalize_email_without_smtp.png"
- **text:** "Finalize the email without SMTP settings."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `finalize_email_without_smtp`

### 17. Send Email without SMTP
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "send_email_without_smtp.png"
- **instructions:** "Send the email without SMTP settings."
- **model:** "gpt-3.5-turbo"
- **schema:** "send_email_without_smtp.png"
- **text:** "Send the email without SMTP settings."
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2
- **retry_interval:** 5
- **output_var:** `send_email_without_smtp`

### 18. Email with SMTP (Dry Run)
- **base_url:** "https://api.bankofthailand.com"
- **image_path:** "email_with_smtp_dry_run.png"
- **instructions:** "Perform a dry run with SMTP settings to test the email sending."
- **model:** "gpt-3.5-turbo"
- **schema:** "email_with_smtp_dry_run.png"
- **text:** "Perform a dry run with SMTP settings to test the email sending."
- **timeout:** 60
- **on_error:**
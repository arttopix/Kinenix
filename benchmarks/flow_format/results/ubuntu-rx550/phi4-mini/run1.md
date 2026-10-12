```markdown
# Collect Bank of Thailand Buying Transfer Rates

> Collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.

## Variables
- `name`: `config`
- `currency_filter`: `#dropdownCurrency`
- `date_field`: `#dateField`
- `period_column`: `#PeriodColumn`
- `buying_rate_column`: `#BuyingRatesTransferColumn`
- `date_format`: `YYYY-MM-DD`
- `currency_column`: `Currency`
- `date_column`: `Date`
- `buying_transfer_rate_column`: `Buying Transfer Rate`
- `csv_file_path`: `${config.output_path}/rates.csv`
- `email_subject`: `${config.email.subject}`
- `email_body`: `${config.email.body}`
- `email_html`: `${config.email.html}`
- `smtp_host`: `smtp.gmail.com`
- `smtp_port`: 587
- `smtp_user`: `your_email@gmail.com`
- `smtp_password`: `your_password`
- `use_tls`: true
- `dry_run`: false
- `max_retries`: 2
- `retry_interval`: 5

## Steps

### 1. Calculate First and Last Day of Report Month
- **date.calc**
  - **date**: `${config.month.date}`
  - **input_format**: `%Y-%m-%d`
  - **add_months**: `${config.month.add_months}`
  - **snap**: true
  - **format**: `YYYY-MM`
  - **output_var**: `start_date, end_date`

### 2. Open Website
- **web.open**
  - **url**: `${config.url}`
  - **headless**: true
  - **timeout**: 10

### 3. Accept Cookie Banner
- **web.click**
  - **selector**: `Accept recommended cookies button`
  - **label**: `Accept recommended cookies`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5

### 4. Filter Currencies
- **logic.loop**
  - **items**: `config.currencies`
  - **item_var**: `currencies`
  - **Sub-steps:**
    - **web.hover**
      - **selector**: `currency filter`
      - **label**: `.currency-filter input[name='currencyCheck'][value='<currency>']`
      - **on_error**: retry
      - **max_retries**: 2
      - **retry_interval**: 5
    - **web.uncheck**
      - **selector**: `currency filter`
      - **label**: `uncheck currency filter`
      - **on_error**: retry
      - **max_retries**: 2
      - **retry_interval**: 5
- **web.download**
  - **selector**: `currency filter`
  - **label**: `Download CSV`
  - **target_path**: `currency_rates.csv`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5

### 5. Pick Start and End Dates
- **web.click**
  - **selector**: `Start date picker`
  - **label**: `Start Date`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5
- **web.click**
  - **selector**: `End date picker`
  - **label**: `End Date`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5

### 6. Search for Rates
- **web.click**
  - **selector**: `button.historical-btn`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5

### 7. Read and Write Rates for Each Currency
- **logic.loop**
  - **items**: `config.currencies`
  - **item_var**: `currencies`
  - **Sub-steps:**
    - **web.get_text**
      - **selector**: `currency tab`
      - **label**: `Currency Name`
      - **output_var**: `currencies`
    - **web.click**
      - **selector**: `currency tab`
      - **label**: `Currency Name`
      - **on_error**: retry
      - **max_retries**: 2
      - **retry_interval**: 5
    - **web.get_table**
      - **selector**: `currency table`
      - **columns**: `["Period", "Buying Rates Transfer"]`
      - **add_columns**: `[["Currency"]]`
      - **min_rows**: 1
      - **output_var**: `currency_rates`
- **csv.write**
  - **file_path**: `${config.output_path}/currency_rates.csv`
  - **data**: `currency_rates`
  - **columns**: `["Currency", "Date", "Buying Transfer Rate"]`
  - **on_error**: retry
  - **max_retries**: 2
  - **retry_interval**: 5

### 8. Close Browser
- **web.close**

### 9. Email CSV File
- **email.send**
  - **to**: `${config.email.to}`
  - **cc**: 
  - **bcc**: 
  - **subject**: `${email_subject}`
  - **body**: 
  - **html**: 
  - **attachments**: `${csv_file_path}`
  - **smtp_host**: `smtp.gmail.com`
  - **smtp_port**: 587
  - **smtp_user**: `your_email@gmail.com`
  - **smtp_password**: `your_password`
  - **use_tls**: true
  - **dry_run**: false
  - **max_retries**: 2
  - **retry_interval**: 5
```
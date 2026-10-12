# Collect Bank of Thailand Buying Transfer Rates

## Variables
- `start_date`: ""
- `end_date`: ""
- `table_data`: []
- `file_path`: "${config.output_path}"

## Steps

### 1. Calculate Dates (`date.calc`)
- **date:** ${config.month.date}
- **add_months:** ${config.month.add_months}
- **format:** %Y-%m-%d
- **output_var:** start_date
- **on_error:** retry
- **max_retries:** 2

### 2. Calculate Dates (`date.calc`)
- **date:** ${config.month.date}
- **add_months:** ${config.month.add_months}
- **add_days:** 30
- **format:** %Y-%m-%d
- **output_var:** end_date
- **on_error:** retry
- **max_retries:** 2

### 3. Open Page (`web.open`)
- **url:** ${config.url}
- **headless:** ${config.headless}
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2

### 4. Accept Cookie Banner (`web.click`)
- **selector:** button[aria-label='Accept recommended cookies']
- **timeout:** 10
- **on_error:** continue

### 5. Select Currency Filter (`web.click`)
- **selector:** #dropdownCurrency
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2

### 6. Loop Through Currencies (`logic.loop`)
- **items:** ${config.currencies}
- **item_var:** currency

#### 6.1. Select Currency (`web.select_option`)
- **selector:** .currency-filter input[name='currencyCheck'][value='<currency>']
- **value:** <currency>
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2

#### 6.2. Select Start Date (`web.type`)
- **selector:** .react-datepicker input >> nth=1
- **text:** ${start_date}
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2

#### 6.3. Select End Date (`web.type`)
- **selector:** .react-datepicker input >> nth=1
- **text:** ${end_date}
- **timeout:** 10
- **on_error:** retry
- **max_retries:** 2

#### 6.4. Search (`web.click`)
- **selector:** button.historical-btn
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2

#### 6.5. Wait for Table to Load (`web.wait_for`)
- **selector:** table
- **state:** visible
- **timeout:** 60
- **on_error:** retry
- **max_retries:** 2

#### 6.6. Extract Table Data (`web.get_table`)
- **selector:** table
- **columns:** Period, Buying Rates Transfer
- **numeric_columns:** Buying Rates Transfer
- **add_columns:** Currency
- **min_rows:** 1
- **timeout:** 60
- **output_var:** table_data
- **on_error:** retry
- **max_retries:** 2

### 7. Add Currency to Table Data (`logic.append`)
- **target:** table_data
- **item:** {"Currency": <currency>}
- **extend:** true

### 8. Write CSV (`csv.write`)
- **file_path:** ${config.output_path}
- **data:** ${table_data}
- **columns:** Currency, Date, Buying Transfer Rate
- **encoding:** utf-8
- **on_error:** retry
- **max_retries:** 2

### 9. Close Browser (`web.close`)
- **on_error:** continue

### 10. Send Email (`email.send`)
- **to:** ${config.email.to}
- **subject:** ${config.email.subject}
- **body:** ${config.email.body}
- **attachments:** ${file_path}
- **smtp_host:** smtp.gmail.com
- **smtp_port:** 587
- **smtp_user:** your-email@gmail.com
- **smtp_password:** your-password
- **use_tls:** true
- **dry_run:** ${config.email.dry_run}
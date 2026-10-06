# RPA Challenge Solver
> Description: Self-Contained Project Bundle: Automate filling RPA Challenge form (10 rounds, 70 fields) from local bundle assets.
> Version: 1.0.0

## Variables
- `non_programmers`: []

## Steps

### 1. Open RPA Challenge Webpage (`web.open`)
- **url:** `${config.website}`
- **headless:** false

### 2. Read Challenge Excel File (`excel.read`)
- **file_path:** `${config.excel_path}`
- **clean_headers:** true
- **output_var:** `challenge_data`

### 3. Click START Button to Begin Timer (`web.click`)
- **selector:** `button:has-text('Start')`

### 4. Loop Through 10 Rows and Process Roles (`logic.loop`)
- **items:** `${challenge_data}`
- **item_var:** `row`
- **Sub-steps:**
  - Check If Role in Company is Programmer (`logic.if`):
    - **left:** `${row.Role in Company}`
    - **operator:** `equals`
    - **right:** `Programmer`
    - **Sub-steps:**
      - Fill First Name (`web.type`):
        - **label:** `First Name`
        - **text:** `${row.First Name}`
      - Fill Last Name (`web.type`):
        - **label:** `Last Name`
        - **text:** `${row.Last Name}`
      - Fill Company Name (`web.type`):
        - **label:** `Company Name`
        - **text:** `${row.Company Name}`
      - Fill Role in Company (`web.type`):
        - **label:** `Role in Company`
        - **text:** `${row.Role in Company}`
      - Fill Address (`web.type`):
        - **label:** `Address`
        - **text:** `${row.Address}`
      - Fill Email (`web.type`):
        - **label:** `Email`
        - **text:** `${row.Email}`
      - Fill Phone Number (`web.type`):
        - **label:** `Phone Number`
        - **text:** `${row.Phone Number}`
      - Submit Form Round (`web.click`):
        - **selector:** `//input[@value='Submit']`
    - **Else-steps:**
      - Collect Non-Programmer into DataTable (`logic.append`):
        - **target:** `non_programmers`
        - **item:** `{"First Name": "${row.First Name}", "Role in Company": "${row.Role in Company}"}`

### 5. Take Screenshot of Result (`web.screenshot`)
- **path:** `${config.screenshot_path}`

### 6. Close Browser (`web.close`)

### 7. Send Email Notification via Gmail (`flow.call`)
- **condition:** `${config.send_notification} == true`
- **output_var:** `email_notification_result`
- **flow:** `@shared/send_email.json`
- **inputs:** `{"to": "${config.email_to}", "subject": "${config.email_subject}", "body": "Hello,\n\nThe RPA Challenge benchmark automation has completed successfully.\nNon-programmers collected: ${non_programmers}\n\nPlease find attached the result screenshot.", "attachments": ["${config.screenshot_path}"], "dry_run": "${config.dry_run}"}`

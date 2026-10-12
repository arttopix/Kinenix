# RPA Challenge Solver
> Description: Automate filling RPA Challenge form (10 rounds, 70 fields) from challenge.xlsx with dynamic layout
> Version: 1.0.0

## Variables
- `target_url`: https://rpachallenge.com/
- `excel_path`: examples/challenge.xlsx
- `screenshot_path`: examples/result_rpachallenge.png

## Steps

### 1. Open RPA Challenge Webpage (`web.open`)
- **url:** ${target_url}
- **headless:** true

### 2. Read Challenge Excel File (`excel.read`)
- **output_var:** `challenge_data`
- **file_path:** ${excel_path}
- **clean_headers:** true

### 3. Click START Button to Begin Timer (`web.click`)
- **selector:** button:has-text('Start')

### 4. Loop Through 10 Rows and Fill Form (`logic.loop`)
- **items:** ${challenge_data}
- **item_var:** row
- **Sub-steps:**
  - Fill First Name (`web.type`):
    - **label:** First Name
    - **text:** ${row.First Name}
  - Fill Last Name (`web.type`):
    - **label:** Last Name
    - **text:** ${row.Last Name}
  - Fill Company Name (`web.type`):
    - **label:** Company Name
    - **text:** ${row.Company Name}
  - Fill Role in Company (`web.type`):
    - **label:** Role in Company
    - **text:** ${row.Role in Company}
  - Fill Address (`web.type`):
    - **label:** Address
    - **text:** ${row.Address}
  - Fill Email (`web.type`):
    - **label:** Email
    - **text:** ${row.Email}
  - Fill Phone Number (`web.type`):
    - **label:** Phone Number
    - **text:** ${row.Phone Number}
  - Submit Form Round (`web.click`):
    - **selector:** //input[@value='Submit']

### 5. Read Congratulations Score Message (`web.get_text`)
- **output_var:** `score_result`
- **selector:** //div[contains(@class, 'congratulations') or contains(@class, 'message2')]

### 6. Take Screenshot of Result (`web.screenshot`)
- **path:** ${screenshot_path}

### 7. Close Browser (`web.close`)

# Kinenix Actions Reference Guide

This document provides a comprehensive specification of standard actions available in Kinenix. In accordance with the **Dual-Representation Lifecycle** (`docs/flow_markdown_spec.md`), each action contains parameter specifications, return types, and dual examples: the authoring **Markdown (`flow.md`)** syntax as primary, followed by the compiled runtime **JSON (`flow.json`)**.

---

## Table of Contents

1. [Web Automation (`web.*`)](#web-automation-web)
   - [web.open](#webopen)
   - [web.click](#webclick)
   - [web.type](#webtype)
   - [web.get_text](#webget_text)
   - [web.get_attribute](#webget_attribute)
   - [web.get_table](#webget_table)
   - [web.wait_for](#webwait_for)
   - [web.is_visible](#webis_visible)
   - [web.press](#webpress)
   - [web.scroll](#webscroll)
   - [web.hover](#webhover)
   - [web.switch_tab](#webswitch_tab)
   - [web.select_option](#webselect_option)
   - [web.upload_file](#webupload_file)
   - [web.check](#webcheck)
   - [web.uncheck](#webuncheck)
   - [web.download](#webdownload)
   - [web.screenshot](#webscreenshot)
   - [web.close](#webclose)
2. [Data, Excel, and CSV (`excel.*`, `csv.*`)](#data-excel-and-csv-excel-csv)
   - [excel.read](#excelread)
   - [excel.write](#excelwrite)
   - [csv.read](#csvread)
   - [csv.write](#csvwrite)
3. [File System Operations (`file.*`)](#file-system-operations-file)
   - [file.exists](#fileexists)
   - [file.copy](#filecopy)
   - [file.move](#filemove)
   - [file.delete](#filedelete)
   - [file.zip](#filezip)
   - [file.unzip](#fileunzip)
   - [file.list](#filelist)
   - [file.read_text](#fileread_text)
   - [file.write_text](#filewrite_text)
   - [file.create_folder](#filecreate_folder)
4. [Control Flow and Logic (`logic.*`)](#control-flow-and-logic-logic)
   - [logic.set_variable](#logicset_variable)
   - [logic.delay](#logicdelay)
   - [logic.if](#logicif)
   - [logic.loop](#logicloop)
   - [logic.append](#logicappend)
5. [Dates (`date.*`)](#dates-date)
   - [date.calc](#datecalc)
6. [HTTP API Integration (`http.*`)](#http-api-integration-http)
   - [http.request](#httprequest)
   - [http.download](#httpdownload)
7. [Modular Subflows and Flow Control (`flow.*`)](#modular-subflows-and-flow-control-flow)
   - [flow.call](#flowcall)
   - [flow.return](#flowreturn)
   - [flow.fail](#flowfail)
8. [Email Notification (`email.*`)](#email-notification-email)
   - [email.send](#emailsend)
9. [AI and Local LLM (`ai.*`)](#ai-and-local-llm-ai)
   - [ai.prompt](#aiprompt)
   - [ai.extract](#aiextract)
   - [ai.decide](#aidecide)

---

## Web Automation (`web.*`)

Powered by Playwright with automatic browser binary installation.

### `web.open`
Launches a browser instance and navigates to a target URL.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | Yes | - | URL of the website to open. If the parameter is given but resolves to an empty value (for example `${config.url}` with no config loaded), the step fails instead of opening a blank page |
| `headless` | boolean | No | `false` | Run browser in headless mode |
| `timeout` | number | No | `30000` | Navigation timeout in milliseconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_open. Open Target Website (`web.open`)
- **url:** https://rpachallenge.com/
- **headless:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_open",
  "name": "Open Target Website",
  "action": "web.open",
  "parameters": {
    "url": "https://rpachallenge.com/",
    "headless": true
  }
}
```

---

### `web.click`
Clicks an element identified by CSS selector, XPath, or adjacent label text.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label text preceding the input element |
| `timeout` | number | No | `30000` | Maximum wait timeout for element to be actionable in milliseconds |
| `optional` | boolean | No | `false` | If `true`, suppresses exceptions if click fails or times out (returns `status: "skipped"`) |
| `wait_for_response` | string | No | - | Part of a URL the click is expected to request. The step ends only when a matching response arrives, so the next step reads the new data instead of relying on `logic.delay`. Find the URL in the browser's DevTools Network tab |
| `response_timeout` | number | No | `timeout` | Milliseconds to wait for that response |

With `wait_for_response`, the step returns `{"status": "clicked", "response_url": ..., "response_status": 200}`.

**Example in `flow.md` (Markdown):**
```markdown
### step_click_submit. Click Submit Button (`web.click`)
- **selector:** //input[@value='Submit']

### step_search. Search And Wait For Results (`web.click`)
- **selector:** `button.search`
- **wait_for_response:** /api/search
- **response_timeout:** 20000
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "step_click_submit",
    "name": "Click Submit Button",
    "action": "web.click",
    "parameters": {
      "selector": "//input[@value='Submit']"
    }
  },
  {
    "id": "step_search",
    "name": "Search And Wait For Results",
    "action": "web.click",
    "parameters": {
      "selector": "button.search",
      "wait_for_response": "/api/search",
      "response_timeout": 20000
    }
  }
]
```

---

### `web.type`
Fills text into an input or textarea element.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `text` | string | Yes | `""` | Text to enter into the field |
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Case-sensitive label text matching preceding element |

**Example in `flow.md` (Markdown):**
```markdown
### step_type_name. Fill First Name (`web.type`)
- **label:** First Name
- **text:** ${row.First Name}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_type_name",
  "name": "Fill First Name",
  "action": "web.type",
  "parameters": {
    "label": "First Name",
    "text": "${row.First Name}"
  }
}
```

---

### `web.get_text`
Extracts visible inner text from a target element.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label identifier |

**Example in `flow.md` (Markdown):**
```markdown
### step_read_score. Read Score Message (`web.get_text`)
- **output_var:** `final_score`
- **selector:** //div[contains(@class, 'congratulations')]
```

**Compiled `flow.json`:**
```json
{
  "id": "step_read_score",
  "name": "Read Score Message",
  "action": "web.get_text",
  "parameters": {
    "selector": "//div[contains(@class, 'congratulations')]"
  },
  "output_var": "final_score"
}
```

---

### `web.get_attribute`
Extracts an HTML attribute value (such as `href`, `src`, `value`, `class`, or `data-*`) from a target element.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `attribute` | string | Yes | - | Name of attribute to extract (e.g. `"href"`, `"src"`, `"value"`) |
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label identifier |

**Example in `flow.md` (Markdown):**
```markdown
### step_get_link. Extract Download Link (`web.get_attribute`)
- **output_var:** `file_url`
- **selector:** a.download-button
- **attribute:** href
```

**Compiled `flow.json`:**
```json
{
  "id": "step_get_link",
  "name": "Extract Download Link",
  "action": "web.get_attribute",
  "parameters": {
    "selector": "a.download-button",
    "attribute": "href"
  },
  "output_var": "file_url"
}
```

---

### `web.get_table`
Reads an HTML `<table>` into a list of rows, one dictionary per row keyed by the header cells (`<thead> <th>`, or the first row when there is no header). Empty rows are skipped and cell text is trimmed. When the selector matches several tables, the first is used; add `:visible` to read the table currently shown (for example in tabs).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath of the table |
| `label` | string | Either | - | Label identifier |
| `columns` | list / dict | No | all columns | A list keeps only those columns, in that order. A dict keeps and renames them (`{"Source Header": "New Name"}`). A missing column fails the step and lists the actual headers |
| `numeric_columns` | list | No | `[]` | Columns (after renaming) converted to numbers; thousands separators are removed, and blank or `-` cells become empty. Text that is not a number fails the step |
| `add_columns` | dict | No | `{}` | Fixed values added as the first columns of every row, for example the currency a table belongs to |
| `min_rows` | number | No | `0` | Fail the step when fewer rows are found, so an empty result stops the flow instead of producing an empty report |
| `timeout` | number | No | `30000` | Milliseconds to wait for the table to exist |

**Example in `flow.md` (Markdown):**
```markdown
### step_read_rates. Read Currency Table (`web.get_table`)
- **output_var:** `currency_rows`
- **selector:** `.results table:visible`
- **columns:** {"Period": "Date", "Buying Rates Transfer": "Buying Transfer Rate"}
- **numeric_columns:** ["Buying Transfer Rate"]
- **add_columns:** {"Currency": "${currency}"}
- **min_rows:** 1
```

**Compiled `flow.json`:**
```json
{
  "id": "step_read_rates",
  "name": "Read Currency Table",
  "action": "web.get_table",
  "parameters": {
    "selector": ".results table:visible",
    "columns": {"Period": "Date", "Buying Rates Transfer": "Buying Transfer Rate"},
    "numeric_columns": ["Buying Transfer Rate"],
    "add_columns": {"Currency": "${currency}"},
    "min_rows": 1
  },
  "output_var": "currency_rows"
}
```

Returns, for example: `[{"Currency": "USD", "Date": "30 Dec 2024", "Buying Transfer Rate": 33.8296}, ...]`.

---

### `web.wait_for`
Waits for an element to satisfy a desired state (or performs an explicit pause).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Optional | - | Target element CSS selector or XPath |
| `label` | string | Optional | - | Target element label |
| `state` | string | No | `"visible"` | Expected state: `"visible"`, `"attached"`, `"detached"`, `"hidden"` |
| `timeout` | number | No | `30000` | Maximum wait timeout in milliseconds |

*Note:* If neither `selector` nor `label` is specified, `web.wait_for` acts as a browser-synchronized pause for `timeout` milliseconds.

**Example in `flow.md` (Markdown):**
```markdown
### step_wait_modal. Wait For Success Modal (`web.wait_for`)
- **selector:** #success-dialog
- **state:** visible
- **timeout:** 15000
```

**Compiled `flow.json`:**
```json
{
  "id": "step_wait_modal",
  "name": "Wait For Success Modal",
  "action": "web.wait_for",
  "parameters": {
    "selector": "#success-dialog",
    "state": "visible",
    "timeout": 15000
  }
}
```

---

### `web.is_visible`
Checks if an element is currently visible on the page within an optional timeout. Returns a boolean (`true` or `false`) without raising an exception. Useful for conditional branching (e.g. cookie consent banners, optional modals).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Target element by adjacent label |
| `timeout` | number | No | `2000` | Max milliseconds to wait for the element to become visible. If `<= 0`, checks immediately. |

**Example in `flow.md` (Markdown):**
```markdown
### step_check_cookie_banner. Check Cookie Banner Visibility (`web.is_visible`)
- **output_var:** `has_cookie_banner`
- **selector:** button:has-text('Accept recommended cookies')
- **timeout:** 2000
```

**Compiled `flow.json`:**
```json
{
  "id": "step_check_cookie_banner",
  "name": "Check Cookie Banner Visibility",
  "action": "web.is_visible",
  "parameters": {
    "selector": "button:has-text('Accept recommended cookies')",
    "timeout": 2000
  },
  "output_var": "has_cookie_banner"
}
```

---

### `web.press`
Sends a keyboard key press or key combination to a specific element or to the active page.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `key` | string | Yes | - | Key name or chord (e.g. `"Enter"`, `"Tab"`, `"Escape"`, `"Control+A"`) |
| `selector` | string | Optional | - | Specific element to receive keystroke (omitted for global page) |
| `label` | string | Optional | - | Target element by adjacent label |

**Example in `flow.md` (Markdown):**
```markdown
### step_press_enter. Submit Form via Enter Key (`web.press`)
- **selector:** input#search-box
- **key:** Enter
```

**Compiled `flow.json`:**
```json
{
  "id": "step_press_enter",
  "name": "Submit Form via Enter Key",
  "action": "web.press",
  "parameters": {
    "selector": "input#search-box",
    "key": "Enter"
  }
}
```

---

### `web.scroll`
Scrolls the page in a specified direction or scrolls a specific element into visible view.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `direction` | string | No | `"down"` | Scroll direction: `"down"`, `"up"`, `"bottom"`, `"top"` |
| `amount` | number | No | `500` | Pixels to scroll (when direction is `"down"` or `"up"`) |
| `selector` | string | Optional | - | Scroll this specific element into view |
| `label` | string | Optional | - | Scroll element associated with this label into view |

**Example in `flow.md` (Markdown):**
```markdown
### step_scroll_down. Scroll Down To Load Content (`web.scroll`)
- **direction:** down
- **amount:** 800
```

**Compiled `flow.json`:**
```json
{
  "id": "step_scroll_down",
  "name": "Scroll Down To Load Content",
  "action": "web.scroll",
  "parameters": {
    "direction": "down",
    "amount": 800
  }
}
```

---

### `web.hover`
Hovers the mouse pointer over a target element to trigger dropdowns or tooltip menus.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label identifier |
| `timeout` | number | No | `30000` | Maximum hover timeout in milliseconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_hover_menu. Open Navigation Dropdown (`web.hover`)
- **selector:** .nav-dropdown-trigger
```

**Compiled `flow.json`:**
```json
{
  "id": "step_hover_menu",
  "name": "Open Navigation Dropdown",
  "action": "web.hover",
  "parameters": {
    "selector": ".nav-dropdown-trigger"
  }
}
```

---

### `web.switch_tab`
Switches active focus to another open tab or window in the browser context.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `index` | number | Optional | - | Zero-based index of open tab (`0` for first, `1` for second, `-1` for latest) |
| `url_pattern` | string | Optional | - | Substring or URL pattern matching target tab |
| `title` | string | Optional | - | Case-insensitive substring matching target page title |

*Note:* If no parameters are provided, switches to the most recently opened tab.

**Example in `flow.md` (Markdown):**
```markdown
### step_switch_dashboard. Switch to Dashboard Tab (`web.switch_tab`)
- **url_pattern:** /dashboard
```

**Compiled `flow.json`:**
```json
{
  "id": "step_switch_dashboard",
  "name": "Switch to Dashboard Tab",
  "action": "web.switch_tab",
  "parameters": {
    "url_pattern": "/dashboard"
  }
}
```

---

### `web.download`
Downloads a file by clicking an export button or resolving a direct link.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Yes | - | Element triggering the download or containing `href` |
| `target_path` | string | No | `"downloads/downloaded_file"` | Destination path for saved file |
| `timeout` | number | No | `30000` | Download timeout in milliseconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_download_excel. Download Challenge Excel File (`web.download`)
- **output_var:** `download_info`
- **selector:** //a[contains(text(),'Download Excel')]
- **target_path:** ./assets/challenge.xlsx
```

**Compiled `flow.json`:**
```json
{
  "id": "step_download_excel",
  "name": "Download Challenge Excel File",
  "action": "web.download",
  "parameters": {
    "selector": "//a[contains(text(),'Download Excel')]",
    "target_path": "./assets/challenge.xlsx"
  },
  "output_var": "download_info"
}
```

---

### `web.select_option`
Selects one or more options in an HTML `<select>` dropdown element. Supports automatic semantic AI matching via OpenThai-SystemOne / Ollama to map abbreviations (e.g. "กทม." -> "กรุงเทพมหานคร") against live page options.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression of `<select>` element |
| `label` | string | Either | - | Label identifying the dropdown |
| `value` | string | Optional | - | Option value attribute to select |
| `text` / `label_text` | string | Optional | - | Visible text label of the option to select |
| `index` | number | Optional | - | Zero-based index of option to select |
| `ai_match` | boolean | No | `false` | When `true`, automatically queries all `<option>` items from the element and uses OpenThai-SystemOne to resolve fuzzy/abbreviated text semantically |
| `systemone_url` | string | No | `"http://localhost:8000"` | OpenThai-SystemOne API base URL |
| `fallback_to_ollama` | boolean | No | `true` | Fallback to Ollama if SystemOne server is unreachable |

**Example (Exact Match) in `flow.md` (Markdown):**
```markdown
### step_select_province. Select Province (`web.select_option`)
- **selector:** select#province
- **text:** Bangkok
```

**Compiled `flow.json`:**
```json
{
  "id": "step_select_province",
  "name": "Select Province",
  "action": "web.select_option",
  "parameters": {
    "selector": "select#province",
    "text": "Bangkok"
  }
}
```

**Example (AI Semantic Match) in `flow.md` (Markdown):**
```markdown
### step_select_province_ai. Select Province Semantically (`web.select_option`)
- **selector:** select#province
- **text:** ${row.Province}
- **ai_match:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_select_province_ai",
  "name": "Select Province Semantically",
  "action": "web.select_option",
  "parameters": {
    "selector": "select#province",
    "text": "${row.Province}",
    "ai_match": true
  }
}
```

---

### `web.upload_file`
Sets file paths onto an HTML `<input type="file">` upload element.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression of `<input type="file">` |
| `label` | string | Either | - | Adjacent label identifier |
| `file_path` | string | Yes | - | Path to file to upload (resolved relative to flow bundle or absolute) |

**Example in `flow.md` (Markdown):**
```markdown
### step_upload_tax_form. Upload Tax Form Document (`web.upload_file`)
- **selector:** input#file-upload
- **file_path:** ./assets/tax_form_2026.pdf
```

**Compiled `flow.json`:**
```json
{
  "id": "step_upload_tax_form",
  "name": "Upload Tax Form Document",
  "action": "web.upload_file",
  "parameters": {
    "selector": "input#file-upload",
    "file_path": "./assets/tax_form_2026.pdf"
  }
}
```

---

### `web.check`
Checks an HTML checkbox or selects a radio button.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label identifier |
| `timeout` | number | No | `30000` | Timeout in milliseconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_agree_terms. Agree to Terms and Conditions (`web.check`)
- **selector:** input#agree
```

**Compiled `flow.json`:**
```json
{
  "id": "step_agree_terms",
  "name": "Agree to Terms and Conditions",
  "action": "web.check",
  "parameters": {
    "selector": "input#agree"
  }
}
```

---

### `web.uncheck`
Unchecks an HTML checkbox element.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `selector` | string | Either | - | CSS selector or XPath expression |
| `label` | string | Either | - | Label identifier |
| `timeout` | number | No | `30000` | Timeout in milliseconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_opt_out. Uncheck Marketing Emails (`web.uncheck`)
- **selector:** input#newsletter
```

**Compiled `flow.json`:**
```json
{
  "id": "step_opt_out",
  "name": "Uncheck Marketing Emails",
  "action": "web.uncheck",
  "parameters": {
    "selector": "input#newsletter"
  }
}
```

---

### `web.screenshot`
Captures a screenshot of the current page.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | No | `"screenshot.png"` | Destination file path (relative to bundle or absolute) |
| `full_page` | boolean | No | `false` | Capture complete scrollable page |

**Example in `flow.md` (Markdown):**
```markdown
### step_capture. Capture Page Screenshot (`web.screenshot`)
- **path:** ./assets/result.png
- **full_page:** false
```

**Compiled `flow.json`:**
```json
{
  "id": "step_capture",
  "name": "Capture Page Screenshot",
  "action": "web.screenshot",
  "parameters": {
    "path": "./assets/result.png",
    "full_page": false
  }
}
```

---

### `web.close`
Closes current page, browser context, and terminates Playwright session.

**Parameters:** None.

**Example in `flow.md` (Markdown):**
```markdown
### step_close_browser. Close Browser Session (`web.close`)
```

**Compiled `flow.json`:**
```json
{
  "id": "step_close_browser",
  "name": "Close Browser Session",
  "action": "web.close",
  "parameters": {}
}
```

---

## Data, Excel, and CSV (`excel.*`, `csv.*`)

Provides zero-license tabular data processing via Pandas and OpenPyXL.

### `excel.read`
Reads an Excel sheet into an in-memory list of dictionaries (records). Empty cells are `None` (never `NaN`), and a column of whole numbers stays whole even when some cells are empty (`2023`, not `2023.0`).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file_path` | string | Yes | - | Path to .xlsx or .xls file (relative paths resolved against bundle) |
| `sheet_name` | string / int | No | `0` | Sheet name or index to read |
| `clean_headers` | boolean | No | `true` | Strip leading and trailing whitespace from column names |
| `as_text` | boolean | No | `false` | Return every cell as text, with `""` for empty cells |

**Example in `flow.md` (Markdown):**
```markdown
### step_read_excel. Read Excel Data (`excel.read`)
- **output_var:** `challenge_data`
- **file_path:** ./assets/challenge.xlsx
- **clean_headers:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_read_excel",
  "name": "Read Excel Data",
  "action": "excel.read",
  "parameters": {
    "file_path": "./assets/challenge.xlsx",
    "clean_headers": true
  },
  "output_var": "challenge_data"
}
```

---

### `excel.write`
Writes a list of dictionaries or single dictionary to an Excel spreadsheet. A relative `file_path` is resolved against the flow bundle directory, like `csv.write`, and missing folders are created. Rows are written in the order given, so group them before writing (for example by appending one currency at a time).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file_path` | string | Yes | - | Output path for generated Excel workbook |
| `data` | list / dict | Yes | `[]` | List of dictionaries or data records to export |
| `sheet_name` | string | No | `"Sheet1"` | Destination sheet name |
| `columns` | list | No | data order | Column order; columns missing from the data are added empty |

**Example in `flow.md` (Markdown):**
```markdown
### step_save_audit. Save Non-Programmers Audit Report (`excel.write`)
- **file_path:** ./output/non_programmers_audit.xlsx
- **data:** ${non_programmers}
- **sheet_name:** AuditReport
- **columns:** ["First Name", "Role in Company"]
```

**Compiled `flow.json`:**
```json
{
  "id": "step_save_audit",
  "name": "Save Non-Programmers Audit Report",
  "action": "excel.write",
  "parameters": {
    "file_path": "./output/non_programmers_audit.xlsx",
    "data": "${non_programmers}",
    "sheet_name": "AuditReport",
    "columns": ["First Name", "Role in Company"]
  }
}
```

---

### `csv.read`
Reads a delimiter-separated text file (CSV, TSV, semicolon-separated) into a list of dictionaries. Each column gets one type from its values:

| Column values | Result |
|---|---|
| All whole numbers, such as `2023` | `int`; empty cells `None` |
| Numbers with decimals, such as `15434.75` | `float`; empty cells `None` |
| All `true` / `false` (any case) | `bool`; empty cells `None` |
| Anything else, including codes with a leading zero (`0812345678`, `00100`) and text such as `NA` | text exactly as written; empty cells `None` |

A column with a single non-numeric value stays text, so phone numbers, postal codes, and IDs are never turned into numbers. Set `as_text: true` to get every cell as text instead, with `""` for empty cells.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file_path` | string | Yes | - | Path to CSV file (resolved against bundle or absolute) |
| `delimiter` | string | No | `","` | Field separator character (e.g. `","`, `";"`, `"\t"`) |
| `encoding` | string | No | `"utf-8-sig"` | File character encoding. The default also reads files saved by Excel with a byte order mark. Thai files from older systems are often `cp874`; the error message says so when the file cannot be read |
| `clean_headers` | boolean | No | `true` | Strip leading and trailing whitespace from column headers |
| `as_text` | boolean | No | `false` | Return every cell as text, with `""` for empty cells |

**Example in `flow.md` (Markdown):**
```markdown
### step_read_csv. Load Customer Records (`csv.read`)
- **output_var:** `customers`
- **file_path:** ./data/customers.csv
- **delimiter:** ,
- **clean_headers:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_read_csv",
  "name": "Load Customer Records",
  "action": "csv.read",
  "parameters": {
    "file_path": "./data/customers.csv",
    "delimiter": ",",
    "clean_headers": true
  },
  "output_var": "customers"
}
```

---

### `csv.write`
Exports a list of dictionaries or single record to a CSV file. By default the file starts with a UTF-8 byte order mark, so Excel shows Thai and other non-English text correctly when the file is opened by double-clicking. Set `encoding: utf-8` for a system that does not accept the mark.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `file_path` | string | Yes | - | Output CSV file path |
| `data` | list / dict | Yes | `[]` | Records to export |
| `columns` | list | No | `null` | Explicit list and order of column names |
| `encoding` | string | No | `"utf-8-sig"` | File character encoding; `utf-8-sig` is UTF-8 with a byte order mark for Excel |
| `append` | boolean | No | `false` | Add the rows to the end of an existing file. The header is written only when the file is new or empty; the rows follow the existing file's column order, and a column the file does not have stops the step |

**Example in `flow.md` (Markdown):**
```markdown
### step_export_csv. Export Processed Data to CSV (`csv.write`)
- **file_path:** ./output/results.csv
- **data:** ${results}
- **columns:** ["id", "name", "status", "timestamp"]
```

**Compiled `flow.json`:**
```json
{
  "id": "step_export_csv",
  "name": "Export Processed Data to CSV",
  "action": "csv.write",
  "parameters": {
    "file_path": "./output/results.csv",
    "data": "${results}",
    "columns": ["id", "name", "status", "timestamp"]
  }
}
```

---

## File System Operations (`file.*`)

Built-in operations for file checking, copying, moving, and deletion. Relative paths are automatically resolved relative to the active flow bundle directory (`__flow_dir__`).

### `file.exists`
Checks whether a file or directory exists on the local filesystem, returning a boolean (`true` / `false`).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | File or directory path to check |

**Example in `flow.md` (Markdown):**
```markdown
### step_check_file. Check If Input File Exists (`file.exists`)
- **output_var:** `is_input_ready`
- **path:** ./input/data.csv
```

**Compiled `flow.json`:**
```json
{
  "id": "step_check_file",
  "name": "Check If Input File Exists",
  "action": "file.exists",
  "parameters": {
    "path": "./input/data.csv"
  },
  "output_var": "is_input_ready"
}
```

---

### `file.copy`
Copies a file or an entire directory tree to a target destination.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `source` | string | Yes | - | Source file or folder path |
| `destination` | string | Yes | - | Destination file or folder path |
| `overwrite` | boolean | No | `true` | Overwrite destination if it already exists |

**Example in `flow.md` (Markdown):**
```markdown
### step_backup_file. Backup Report (`file.copy`)
- **source:** ./output/report.xlsx
- **destination:** ./backups/report_backup.xlsx
- **overwrite:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_backup_file",
  "name": "Backup Report",
  "action": "file.copy",
  "parameters": {
    "source": "./output/report.xlsx",
    "destination": "./backups/report_backup.xlsx",
    "overwrite": true
  }
}
```

---

### `file.move`
Moves or renames a file or directory.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `source` | string | Yes | - | Source file or folder path |
| `destination` | string | Yes | - | Destination file or folder path |
| `overwrite` | boolean | No | `true` | Overwrite destination if it already exists |

**Example in `flow.md` (Markdown):**
```markdown
### step_archive_file. Move Processed File to Archive (`file.move`)
- **source:** ./input/orders.csv
- **destination:** ./archive/orders_processed.csv
- **overwrite:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_archive_file",
  "name": "Move Processed File to Archive",
  "action": "file.move",
  "parameters": {
    "source": "./input/orders.csv",
    "destination": "./archive/orders_processed.csv",
    "overwrite": true
  }
}
```

---

### `file.delete`
Deletes a file or recursively removes a directory.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | Path of file or directory to remove |
| `missing_ok` | boolean | No | `true` | Do not raise an error if target path does not exist |

**Example in `flow.md` (Markdown):**
```markdown
### step_cleanup_temp. Delete Temporary Files (`file.delete`)
- **path:** ./temp/working_cache.tmp
- **missing_ok:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_cleanup_temp",
  "name": "Delete Temporary Files",
  "action": "file.delete",
  "parameters": {
    "path": "./temp/working_cache.tmp",
    "missing_ok": true
  }
}
```

---

### `file.zip`
Packs files and folders into one zip file (deflate compression), for example to attach everything a run produced to an email. A folder keeps its name as the top level inside the zip, so `./output` is stored as `output/...`. If the zip file lies inside a folder being packed, it is left out, so `./output` can be zipped into `./output/run.zip` on every run. The zip is written under a temporary name first and renamed when complete, so a failure never leaves a half-written file. Paths are relative to the flow folder.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `source` | string or list | Yes | - | A file or folder, or a list of files and folders. Two entries that would be stored under the same name (for example two `report.csv` files) stop the step with an error |
| `destination` | string | Yes | - | Path of the zip file to create; missing parent folders are created |
| `overwrite` | boolean | No | `true` | Replace an existing zip file. With `false`, an existing file stops the step |

**Example in `flow.md` (Markdown):**
```markdown
### 18. Zip Run Output (`file.zip`)
- **source:** ./output
- **destination:** ./outbox/run.zip
- **output_var:** `packed`

### 19. Email Results (`email.send`)
- **to:** `${config.email.to}`
- **subject:** Insurance packages
- **body:** All files from this run are attached.
- **attachments:** ["${packed.zip_path}"]
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "step_18",
    "name": "Zip Run Output",
    "action": "file.zip",
    "parameters": {
      "source": "./output",
      "destination": "./outbox/run.zip"
    },
    "output_var": "packed"
  },
  {
    "id": "step_19",
    "name": "Email Results",
    "action": "email.send",
    "parameters": {
      "to": "${config.email.to}",
      "subject": "Insurance packages",
      "body": "All files from this run are attached.",
      "attachments": ["${packed.zip_path}"]
    }
  }
]
```

**Output Format:**
```json
{
  "zip_path": "/home/user/kinenix-flows/tiph/outbox/run.zip",
  "files_added": 7,
  "size_bytes": 184320,
  "status": "zipped"
}
```

---

### `file.unzip`
Extracts a zip file into a folder. Every entry is checked before anything is written: an entry that would land outside the destination folder (for example `../../etc/passwd`) stops the step, and so does an existing file when `overwrite` is `false`. Paths are relative to the flow folder.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `source` | string | Yes | - | Path of the zip file |
| `destination` | string | No | zip path without `.zip` | Folder to extract into; created if missing. `./inbox/orders.zip` extracts into `./inbox/orders` by default |
| `overwrite` | boolean | No | `true` | Replace files that already exist in the destination |

**Example in `flow.md` (Markdown):**
```markdown
### 2. Extract Received Orders (`file.unzip`)
- **source:** ./inbox/orders.zip
- **destination:** ./work/orders
- **output_var:** `extracted`
```

**Compiled `flow.json`:**
```json
{
  "id": "step_2",
  "name": "Extract Received Orders",
  "action": "file.unzip",
  "parameters": {
    "source": "./inbox/orders.zip",
    "destination": "./work/orders"
  },
  "output_var": "extracted"
}
```

**Output Format:**
```json
{
  "destination": "/home/user/kinenix-flows/orders/work/orders",
  "files": ["orders_2026-10.csv", "notes/readme.txt"],
  "files_extracted": 2,
  "status": "unzipped"
}
```

---

### `file.list`
Lists the files or folders in a folder, so a flow can loop over them with `logic.loop` (for example every CSV that arrived in an inbox) or pick the newest one. Each item carries its name, path, size, and modification time, so no separate "file info" action is needed. Paths are relative to the flow folder. An empty result is an empty list, which a `logic.if` or the `condition` of `flow.fail` can check.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | Folder to list; a missing folder stops the step |
| `pattern` | string | No | `*` | File name pattern, for example `*.csv` or `orders_2026-*.xlsx` |
| `recursive` | boolean | No | `false` | Also look in subfolders; `relative_path` then includes the subfolder |
| `type` | string | No | `files` | `files`, `folders`, or `all` |
| `sort_by` | string | No | `name` | `name`, `modified`, or `size` |
| `descending` | boolean | No | `false` | Reverse the order, for example newest or largest first |
| `limit` | integer | No | - | Keep only the first N items after sorting; `1` with `sort_by: modified` and `descending: true` gives the newest file |

**Example in `flow.md` (Markdown):**
```markdown
### 1. Find Order Files (`file.list`)
- **path:** ./inbox
- **pattern:** *.csv
- **sort_by:** modified
- **output_var:** `files`

### 2. Handle Each File (`logic.loop`)
- **items:** `${files}`
- **item_var:** `f`
- **Sub-steps:**
  - Read Orders (`csv.read`):
    - **file_path:** `${f.path}`
    - **output_var:** `orders`
  - Move To Archive (`file.move`):
    - **source:** `${f.path}`
    - **destination:** ./archive/${f.name}
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "step_1",
    "name": "Find Order Files",
    "action": "file.list",
    "parameters": {
      "path": "./inbox",
      "pattern": "*.csv",
      "sort_by": "modified"
    },
    "output_var": "files"
  },
  {
    "id": "step_2",
    "name": "Handle Each File",
    "action": "logic.loop",
    "parameters": {
      "items": "${files}",
      "item_var": "f"
    },
    "sub_steps": [
      {
        "id": "sub_step_2_1",
        "name": "Read Orders",
        "action": "csv.read",
        "parameters": {
          "file_path": "${f.path}"
        },
        "output_var": "orders"
      },
      {
        "id": "sub_step_2_2",
        "name": "Move To Archive",
        "action": "file.move",
        "parameters": {
          "source": "${f.path}",
          "destination": "./archive/${f.name}"
        }
      }
    ]
  }
]
```

**Output Format** (one item per file):
```json
[
  {
    "name": "orders_2026-10.csv",
    "stem": "orders_2026-10",
    "extension": ".csv",
    "path": "/home/user/kinenix-flows/orders/inbox/orders_2026-10.csv",
    "relative_path": "orders_2026-10.csv",
    "is_folder": false,
    "size": 2048,
    "modified": "2026-10-09T08:15:02"
  }
]
```

---

### `file.read_text`
Reads a text file as one string, as a list of lines, or as parsed JSON, for example an email body template, a JSON file from another system, or a list of IDs one per line. The default encoding also reads files saved with a byte order mark (Excel, Notepad). Paths are relative to the flow folder.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | File to read |
| `format` | string | No | `text` | `text` returns one string; `lines` returns a list of lines without line breaks (ready for `logic.loop`); `json` returns the parsed object or list |
| `encoding` | string | No | `utf-8-sig` | Text encoding. Thai files from older Windows systems are usually `cp874` (or `tis-620`); the error message suggests this when UTF-8 fails |

**Example in `flow.md` (Markdown):**
```markdown
### 3. Read Email Template (`file.read_text`)
- **path:** ./assets/email_body.txt
- **output_var:** `email_body`

### 4. Read Policy List (`file.read_text`)
- **path:** ./inbox/policies.txt
- **format:** lines
- **output_var:** `policy_ids`
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "step_3",
    "name": "Read Email Template",
    "action": "file.read_text",
    "parameters": {
      "path": "./assets/email_body.txt"
    },
    "output_var": "email_body"
  },
  {
    "id": "step_4",
    "name": "Read Policy List",
    "action": "file.read_text",
    "parameters": {
      "path": "./inbox/policies.txt",
      "format": "lines"
    },
    "output_var": "policy_ids"
  }
]
```

---

### `file.write_text`
Writes text to a file, replacing it or adding to its end, for example a run summary, a log line per processed item, or a JSON file for another system. A list or object in `content` is written as formatted JSON (Thai text stays readable). With `append`, the text is added as a line: a line break follows it if it does not already end with one. Missing parent folders are created. Paths are relative to the flow folder.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | File to write |
| `content` | string, list, or object | Yes | - | Text to write; a list or object is written as JSON |
| `append` | boolean | No | `false` | Add to the end of the file as a new line instead of replacing it |
| `encoding` | string | No | `utf-8` | Text encoding, for example `cp874` for a system that only reads Thai Windows encoding |

**Example in `flow.md` (Markdown):**
```markdown
### 7. Log Processed Plan (`file.write_text`)
- **path:** ./output/run_log.txt
- **content:** ${plan.brand} ${plan.model}: ${plan_count} packages
- **append:** true
```

**Compiled `flow.json`:**
```json
{
  "id": "step_7",
  "name": "Log Processed Plan",
  "action": "file.write_text",
  "parameters": {
    "path": "./output/run_log.txt",
    "content": "${plan.brand} ${plan.model}: ${plan_count} packages",
    "append": true
  }
}
```

**Output Format:**
```json
{
  "path": "/home/user/kinenix-flows/tiph/output/run_log.txt",
  "characters_written": 24,
  "mode": "append",
  "status": "written"
}
```

---

### `file.create_folder`
Creates a folder, including any missing parent folders. An existing folder is not an error. Most actions that write files already create their parent folders; use this for a folder that must exist before anything is written into it, for example a per-run folder that a browser download goes to. Paths are relative to the flow folder.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | string | Yes | - | Folder to create. A file with the same name stops the step |

**Example in `flow.md` (Markdown):**
```markdown
### 1. Prepare Screenshot Folder (`file.create_folder`)
- **path:** ./output/screenshots
```

**Compiled `flow.json`:**
```json
{
  "id": "step_1",
  "name": "Prepare Screenshot Folder",
  "action": "file.create_folder",
  "parameters": {
    "path": "./output/screenshots"
  }
}
```

**Output Format:**
```json
{
  "path": "/home/user/kinenix-flows/tiph/output/screenshots",
  "created": true,
  "status": "created"
}
```

---

## Control Flow and Logic (`logic.*`)

Core orchestration primitives for variable manipulation, loops, conditions, and error recovery.

### Step Resilience & Error Handling (`error_handler`)

Every step in Kinenix can define an optional `error_handler` strategy to make execution resilient against transient network hiccups or flaky selectors:

**Configuration Fields:**
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `on_error` | string | No | `"stop"` | Error policy: `"stop"` (fail flow), `"continue"` (record failure and proceed), or `"retry"` (retry step). Business errors (such as from `flow.fail`) are never retried |
| `max_retries` | number | No | `0` | Number of extra attempts after original failure (e.g. `3` = 1 original + 3 retries) |
| `retry_interval` | number | No | `1.0` | Delay in seconds between retry attempts |
| `fallback_step_id` | string | No | `null` | Target step ID to execute as a recovery handler upon step failure |

In `flow.md`, write the fields as ordinary step keys. The compiler moves them into `error_handler`; they are not passed to the action. The JSON form `- **error_handler:** {"on_error": "retry", ...}` is also accepted.

**Example with Retry and Fallback Recovery in `flow.md` (Markdown):**
```markdown
### step_fetch_orders. Fetch Orders API (`http.request`)
- **output_var:** `orders_data`
- **url:** https://api.example.com/orders
- **on_error:** retry
- **max_retries:** 3
- **retry_interval:** 2.0
- **fallback_step_id:** step_use_offline_cache
```

**Compiled `flow.json`:**
```json
{
  "id": "step_fetch_orders",
  "name": "Fetch Orders API",
  "action": "http.request",
  "parameters": {
    "url": "https://api.example.com/orders"
  },
  "output_var": "orders_data",
  "error_handler": {
    "on_error": "retry",
    "max_retries": 3,
    "retry_interval": 2.0,
    "fallback_step_id": "step_use_offline_cache"
  }
}
```

---

### `logic.set_variable`
Assigns a value to a named execution context variable.

**Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Variable name to create or update |
| `value` | any | Yes | Value or evaluated expression |

**Example in `flow.md` (Markdown):**
```markdown
### step_set_counter. Initialize Counter (`logic.set_variable`)
- **name:** processed_count
- **value:** 0
```

**Compiled `flow.json`:**
```json
{
  "id": "step_set_counter",
  "name": "Initialize Counter",
  "action": "logic.set_variable",
  "parameters": {
    "name": "processed_count",
    "value": 0
  }
}
```

---

### `logic.delay`
Pauses execution for a specified duration.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `seconds` | number | No | `1.0` | Sleep duration in seconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_wait. Wait for Page Stabilization (`logic.delay`)
- **seconds:** 2.5
```

**Compiled `flow.json`:**
```json
{
  "id": "step_wait",
  "name": "Wait for Page Stabilization",
  "action": "logic.delay",
  "parameters": {
    "seconds": 2.5
  }
}
```

---

### `logic.if`
Conditionally branches execution into `sub_steps` (when condition evaluates to true) or `else_steps` (when false).

**Supported Operators:**
- `equals`, `==`, `eq`
- `not_equals`, `!=`, `neq`
- `greater_than`, `>`, `gt`
- `greater_than_or_equal`, `>=`, `gte`
- `less_than`, `<`, `lt`
- `less_than_or_equal`, `<=`, `lte`
- `contains`, `not_contains` (right is part of left)
- `in`, `not_in` (left is part of right; with a list, an item equals left)
- `starts_with`, `ends_with`
- `is_empty`, `is_not_empty`

In `condition`, write the operators as words: `contains`, `not contains`, `in`, `not in`, `starts with`, `ends with`, `is empty`, `is not empty` (see [Conditions](flow_markdown_spec.md#c-conditions)).

**Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `left` | any | Yes* | Left-hand operand |
| `operator` | string | No (default: equals) | Comparison operator |
| `right` | any | No | Right-hand operand |
| `condition` | string | Yes* | Alternatively, single expression such as `"${val} == target"` |

*\*Note: Either `left` or `condition` parameter is required.*

**Example in `flow.md` (Markdown):**
```markdown
### sub_check_role. Check If Role is Programmer (`logic.if`)
- **left:** ${row.Role in Company}
- **operator:** equals
- **right:** Programmer
- **Sub-steps:**
  - Fill Form (`web.type`):
    - **label:** First Name
    - **text:** ${row.First Name}
- **Else-steps:**
  - Append to Audit (`logic.append`):
    - **target:** non_programmers
    - **item:** {"First Name": "${row.First Name}", "Role": "${row.Role in Company}"}
```

**Compiled `flow.json`:**
```json
{
  "id": "sub_check_role",
  "name": "Check If Role is Programmer",
  "action": "logic.if",
  "parameters": {
    "left": "${row.Role in Company}",
    "operator": "equals",
    "right": "Programmer"
  },
  "sub_steps": [
    {
      "id": "fill_form",
      "name": "Fill Form",
      "action": "web.type",
      "parameters": { "label": "First Name", "text": "${row.First Name}" }
    }
  ],
  "else_steps": [
    {
      "id": "collect_audit",
      "name": "Append to Audit",
      "action": "logic.append",
      "parameters": {
        "target": "non_programmers",
        "item": { "First Name": "${row.First Name}", "Role": "${row.Role in Company}" }
      }
    }
  ]
}
```

---

### `logic.loop`
Iterates over an array or list of objects, binding each element to an item variable.

**Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `items` | list / string | Yes | Array or variable reference `${var}` to iterate |
| `item_var` | string | No (default: item) | Context variable name representing the current iteration item |

**Example in `flow.md` (Markdown):**
```markdown
### step_loop_rows. Iterate Dataset Rows (`logic.loop`)
- **items:** ${challenge_data}
- **item_var:** row
- **Sub-steps:**
  - Process Row Item (`logic.if`):
    - **left:** ${row.Status}
    - **operator:** equals
    - **right:** Active
```

**Compiled `flow.json`:**
```json
{
  "id": "step_loop_rows",
  "name": "Iterate Dataset Rows",
  "action": "logic.loop",
  "parameters": {
    "items": "${challenge_data}",
    "item_var": "row"
  },
  "sub_steps": [
    {
      "id": "process_row",
      "name": "Process Row Item",
      "action": "logic.if",
      "parameters": {
        "left": "${row.Status}",
        "operator": "equals",
        "right": "Active"
      }
    }
  ]
}
```

---

### `logic.append`
Appends an item, dictionary, or primitive value to a list in context variables. If the target variable does not exist, it initializes an empty list.

**Parameters:**
| Parameter | Type | Required | Description |
|---|---|---|---|
| `target` | string | Yes | Name of the list variable in context |
| `item` | any | Yes | Item or object to append |
| `extend` | boolean | No | When `true`, `item` must be a list and each of its elements is appended (for example the rows returned by `web.get_table`), instead of the list as one item. Default `false` |

**Example in `flow.md` (Markdown):**
```markdown
### append_record. Add Non-Programmer to List (`logic.append`)
- **target:** non_programmers
- **item:** {"First Name": "${row.First Name}", "Role in Company": "${row.Role in Company}"}

### append_rows. Collect Currency Rows (`logic.append`)
- **target:** fx_rows
- **item:** `${currency_rows}`
- **extend:** true
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "append_record",
    "name": "Add Non-Programmer to List",
    "action": "logic.append",
    "parameters": {
      "target": "non_programmers",
      "item": {
        "First Name": "${row.First Name}",
        "Role in Company": "${row.Role in Company}"
      }
    }
  },
  {
    "id": "append_rows",
    "name": "Collect Currency Rows",
    "action": "logic.append",
    "parameters": {
      "target": "fx_rows",
      "item": "${currency_rows}",
      "extend": true
    }
  }
]
```

---

## Dates (`date.*`)

Works out dates relative to the day the flow runs, so a scheduled flow always processes the right period without editing its config.

---

### `date.calc`
Starts from a date (today by default), optionally moves it by days, weeks, months, or years, optionally snaps it to the start or end of a week, month, or year, and returns the result split into parts. Steps in order: read `date`, add `add_years` and `add_months`, add `add_weeks` and `add_days`, then apply `snap`. Month arithmetic keeps the day where it can and otherwise uses the last day of the month (31 March minus one month is 28 or 29 February). "Today" is the worker's local date, so set the machine's time zone correctly.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `date` | string | No | `today` | Starting point: `today` (midnight), `now` (current time), an ISO date or date-time such as `2024-12-01` or `2024-12-01T09:30`, or a date in another format together with `input_format` |
| `input_format` | string | No | - | Python `strptime` pattern for reading `date`, for example `%d/%m/%Y` for `31/12/2024` |
| `add_days` | integer | No | `0` | Days to add; negative moves back |
| `add_weeks` | integer | No | `0` | Weeks to add; negative moves back |
| `add_months` | integer | No | `0` | Months to add; negative moves back |
| `add_years` | integer | No | `0` | Years to add; negative moves back |
| `snap` | string | No | - | `start_of_month`, `end_of_month`, `start_of_year`, `end_of_year`, `start_of_week` (Monday), or `end_of_week` (Sunday) |
| `format` | string | No | `%Y-%m-%d` | Python `strftime` pattern for the `text` field of the result, for example `%d-%m-%Y` or `%Y%m%d_%H%M` |

**Example in `flow.md` (Markdown):**
```markdown
### 1. First Day Of Last Month (`date.calc`)
- **add_months:** -1
- **snap:** start_of_month
- **output_var:** `start`

### 2. Last Day Of Last Month (`date.calc`)
- **add_months:** -1
- **snap:** end_of_month
- **format:** %d-%m-%Y
- **output_var:** `end`

### 3. Choose Start Month (`web.select_option`)
- **selector:** `.react-datepicker select >> nth=0`
- **text:** `${start.month_name}`

### 4. Report File Name (`logic.set_variable`)
- **name:** report_path
- **value:** ./output/fx_${start.year}-${start.month}.csv
```

**Compiled `flow.json`:**
```json
[
  {
    "id": "step_1",
    "name": "First Day Of Last Month",
    "action": "date.calc",
    "parameters": {
      "add_months": -1,
      "snap": "start_of_month"
    },
    "output_var": "start"
  },
  {
    "id": "step_2",
    "name": "Last Day Of Last Month",
    "action": "date.calc",
    "parameters": {
      "add_months": -1,
      "snap": "end_of_month",
      "format": "%d-%m-%Y"
    },
    "output_var": "end"
  },
  {
    "id": "step_3",
    "name": "Choose Start Month",
    "action": "web.select_option",
    "parameters": {
      "selector": ".react-datepicker select >> nth=0",
      "text": "${start.month_name}"
    }
  },
  {
    "id": "step_4",
    "name": "Report File Name",
    "action": "logic.set_variable",
    "parameters": {
      "name": "report_path",
      "value": "./output/fx_${start.year}-${start.month}.csv"
    }
  }
]
```

**Output Format** (run on 8 October 2026, step 2 above):
```json
{
  "text": "30-09-2026",
  "date": "2026-09-30",
  "datetime": "2026-09-30T00:00:00",
  "year": 2026,
  "month": 9,
  "day": 30,
  "month_name": "September",
  "month_abbr": "Sep",
  "weekday": "Wednesday",
  "weekday_number": 3,
  "days_in_month": 30,
  "hour": 0,
  "minute": 0
}
```

Month and weekday names are always English, whatever the machine's language. `weekday_number` runs from 1 (Monday) to 7 (Sunday). `year`, `month`, `day`, `hour`, and `minute` are numbers; inside a longer text such as a selector or file name they appear without leading zeros (`9`, not `09`). Use `text` with `format` when leading zeros are needed.

---

## HTTP API Integration (`http.*`)

Enables direct REST API interaction without external browser overhead.

### `http.request`
Executes an HTTP request and outputs status code, response headers, and body.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | Yes | - | Request URL endpoint |
| `method` | string | No | `"GET"` | HTTP method (GET, POST, PUT, DELETE, PATCH) |
| `headers` | dict | No | `{}` | HTTP request headers |
| `payload` | dict / string | No | `null` | Request body (JSON dict or raw string) |
| `timeout` | number | No | `30` | Request timeout in seconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_send_webhook. Notify Notification Webhook (`http.request`)
- **output_var:** `api_response`
- **url:** https://api.example.com/v1/notify
- **method:** POST
- **headers:** {"Content-Type": "application/json", "Authorization": "Bearer ${env.API_KEY}"}
- **payload:** {"status": "completed", "total_processed": 10}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_send_webhook",
  "name": "Notify Notification Webhook",
  "action": "http.request",
  "parameters": {
    "url": "https://api.example.com/v1/notify",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer ${env.API_KEY}"
    },
    "payload": {
      "status": "completed",
      "total_processed": 10
    }
  },
  "output_var": "api_response"
}
```

---

### `http.download`
Downloads a file from an HTTP/HTTPS URL directly to the filesystem without launching a browser.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | Yes | - | Direct HTTP/HTTPS file URL to download |
| `target_path` | string | Yes | - | Local path to save the downloaded file |
| `timeout` | number | No | `60` | Network download timeout in seconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_download_pdf. Download Invoice PDF (`http.download`)
- **output_var:** `downloaded_file`
- **url:** https://example.com/files/invoice_102.pdf
- **target_path:** ./downloads/invoice_102.pdf
```

**Compiled `flow.json`:**
```json
{
  "id": "step_download_pdf",
  "name": "Download Invoice PDF",
  "action": "http.download",
  "parameters": {
    "url": "https://example.com/files/invoice_102.pdf",
    "target_path": "./downloads/invoice_102.pdf"
  },
  "output_var": "downloaded_file"
}
```

---

## Modular Subflows and Flow Control (`flow.*`)

Enables breaking large enterprise automations into clean, isolated, reusable child flows (subflows) located within the same project bundle or across global `@shared/` components. Adopts **Contract-First Design (`flow.return` + `output_var`)**, matching modern AI agent tool-calling paradigms.

### `flow.call`
Executes an external child flow (subflow) within an isolated context.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `flow` | string | Yes | - | Path to child flow (`./subflows/name.json`, `@shared/name.json`, or alias) |
| `inputs` | dict | No | `{}` | Arguments passed into the subflow (evaluated in parent context) |
| `propagate_sessions` | boolean | No | `true` | Share active Playwright browser sessions with child flow |
| `outputs` | dict | No | `null` | Optional direct mapping from child variables to parent variables |

**Variable Resolution & Priority:**
1. **Subflow Defaults:** Initial variables declared in the subflow definition.
2. **Inputs:** Values explicitly passed via `inputs` parameter (overrides defaults).
3. **System Variables:** Internal paths (`__flow_dir__`, `__parent_flow__`) and shared sessions.

**Safeguards & Protections:**
- **Max Depth:** Enforces maximum call nesting limit (default: 10 levels) to prevent memory exhaustion.
- **Circular Call Detection:** Detects and immediately blocks circular recursion (e.g. A calling B calling A).
- **Browser Safeguard:** If a subflow calls `web.close` while sharing the parent's browser, the engine intercepts the call and protects the parent's active browser session.

**Example in `flow.md` (Markdown):**
```markdown
### step_send_alert. Send Reusable LINE Alert (`flow.call`)
- **output_var:** `alert_result`
- **flow:** @shared/notify_line.json
- **inputs:** {"message": "Invoice #4891 verified successfully", "recipient": "Finance Lead", "alert_level": "SUCCESS"}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_send_alert",
  "name": "Send Reusable LINE Alert",
  "action": "flow.call",
  "parameters": {
    "flow": "@shared/notify_line.json",
    "inputs": {
      "message": "Invoice #4891 verified successfully",
      "recipient": "Finance Lead",
      "alert_level": "SUCCESS"
    }
  },
  "output_var": "alert_result"
}
```

---

### `flow.return`
Stops subflow execution early and returns a structured payload to the caller's `output_var`.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `value` | any | Yes | - | Payload (dict, list, string, number, or boolean) returned to parent flow |

**Example in `flow.md` (Markdown):**
```markdown
### step_return_payload. Return Extracted Data (`flow.return`)
- **value:** {"status": "success", "records_count": "${total_count}", "file_path": "${saved_pdf}"}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_return_payload",
  "name": "Return Extracted Data",
  "action": "flow.return",
  "parameters": {
    "value": {
      "status": "success",
      "records_count": "${total_count}",
      "file_path": "${saved_pdf}"
    }
  }
}
```

---

### `flow.fail`
Stops the flow on purpose with a clear message, usually behind a `condition`. Use it for business exceptions such as missing or invalid data, so the failure says what is wrong instead of a later step failing with a technical error. A `business` failure is recorded with error type `Business` and is never retried, even when the step has `on_error: retry`, because the same data fails the same way. A `continue` or `fallback_step_id` error policy still applies.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | string | Yes | - | Reason recorded as the error message, in the execution log and the Hub |
| `category` | string | No | `"business"` | `"business"` (not retried) or `"technical"` |

**Example in `flow.md` (Markdown):**
```markdown
### step_check_rows. Stop When No Rates Were Found (`flow.fail`)
- **condition:** `${fx_rows} == []`
- **message:** No exchange rates were found for ${config.start_date.month} ${config.start_date.year}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_check_rows",
  "name": "Stop When No Rates Were Found",
  "action": "flow.fail",
  "parameters": {
    "message": "No exchange rates were found for ${config.start_date.month} ${config.start_date.year}"
  },
  "condition": "${fx_rows} == []"
}
```

---

## Email Notification (`email.*`)

Enables sending automated email notifications and attachments via SMTP (e.g. Gmail SMTP, Outlook 365, or local enterprise mail servers).

### `email.send`
Constructs and dispatches an email message with support for plain text, HTML body, attachments, CC, and BCC.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `to` | string / list | Yes | - | Primary recipient email address or list of addresses |
| `subject` | string | No | `"Kinenix Notification"` | Subject line of the email |
| `body` | string | No | `""` | Plain-text email message body |
| `html` | string | No | `null` | Optional rich HTML email body |
| `cc` | string / list | No | `null` | Carbon copy recipient address(es) |
| `bcc` | string / list | No | `null` | Blind carbon copy recipient address(es) |
| `attachments` | list | No | `[]` | List of file paths to attach (relative to flow or absolute) |
| `smtp_host` | string | No | `$SMTP_HOST` or `"smtp.gmail.com"` | SMTP server hostname |
| `smtp_port` | number | No | `$SMTP_PORT` or `587` | SMTP port (587 with STARTTLS) |
| `smtp_user` | string | No | see below | Sender username / email address |
| `smtp_password` | string | No | see below | Sender password or app password |
| `use_tls` | boolean | No | `true` | Establish STARTTLS secure connection |
| `dry_run` | boolean | No | `false` | When true, checks recipients and that every attachment exists, without sending |

Any SMTP provider works; the result's `channel` names the server used, for example `SMTP smtp.office365.com:587`. Keep credentials in environment variables, never in `flow.md` or `config.json`. Without `smtp_user` and `smtp_password` parameters, the action uses `SMTP_USER` and `SMTP_PASSWORD` when `SMTP_USER` is set, otherwise `GMAIL_USER` and `GMAIL_APP_PASSWORD`; the two pairs are never mixed.

| Provider | `SMTP_HOST` | `SMTP_PORT` | Notes |
|---|---|---|---|
| Gmail | `smtp.gmail.com` (default) | `587` | Needs 2-Step Verification and an app password |
| Outlook / Microsoft 365 | `smtp.office365.com` | `587` | Many organizations disable password-based SMTP; ask IT to enable SMTP AUTH for the sending mailbox |
| Company mail server | from IT | from IT | Set `use_tls` to match the server |

The message is `multipart/mixed`: the body (plain text, HTML, or both as alternatives) followed by the attachments. Tests send through a local fake SMTP server and check the recipients, headers, body parts, and attachment bytes.

**Example in `flow.md` (Markdown):**
```markdown
### step_send_report. Send Daily Processing Report (`email.send`)
- **output_var:** `email_result`
- **to:** manager@company.com
- **subject:** Daily RPA Processing Summary - [${status}]
- **body:** |
    Hello,

    The automated workflow has completed successfully.
    Processed records: ${count}
- **attachments:** ["./assets/daily_summary.xlsx"]
- **dry_run:** false
```

**Compiled `flow.json`:**
```json
{
  "id": "step_send_report",
  "name": "Send Daily Processing Report",
  "action": "email.send",
  "parameters": {
    "to": "manager@company.com",
    "subject": "Daily RPA Processing Summary - [${status}]",
    "body": "Hello,\n\nThe automated workflow has completed successfully.\nProcessed records: ${count}",
    "attachments": [
      "./assets/daily_summary.xlsx"
    ],
    "dry_run": false
  },
  "output_var": "email_result"
}
```

---

## AI and Local LLM (`ai.*`)

Integrates local LLMs powered by Ollama (or compatible HTTP endpoints like vLLM) for intelligent unstructured text understanding, zero-shot extraction, and decision making without cloud token costs.

### `ai.prompt`
Sends a prompt to an Ollama model with optional JSON schema enforcement and image inputs.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `prompt` | string | Yes | - | Prompt text or user query |
| `model` | string | No | `"qwen2.5:1.5b"` | Local LLM model tag |
| `system` | string | No | `null` | System instruction prompt |
| `format` | string | No | `null` | Set to `"json"` for structured JSON output |
| `image_path` | string | No | - | Path to one image for vision models, relative to the flow bundle |
| `temperature` | number | No | `0.1` | Sampling temperature |
| `base_url` | string | No | `"http://localhost:11434"` | Ollama service base URL |
| `timeout` | number | No | `60` | Request timeout in seconds |

**Example in `flow.md` (Markdown):**
```markdown
### step_summarize_lead. Classify Lead Intent (`ai.prompt`)
- **output_var:** `lead_analysis`
- **model:** qwen2.5:1.5b
- **prompt:** Classify whether this inquiry is urgent: '${email_body}'
- **format:** json
```

**Compiled `flow.json`:**
```json
{
  "id": "step_summarize_lead",
  "name": "Classify Lead Intent",
  "action": "ai.prompt",
  "parameters": {
    "model": "qwen2.5:1.5b",
    "prompt": "Classify whether this inquiry is urgent: '${email_body}'",
    "format": "json"
  },
  "output_var": "lead_analysis"
}
```

---

### `ai.extract`
Specialized action that extracts structured fields directly from raw unstructured text.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `text` | string | Yes | - | Raw text, email, or OCR string to extract from |
| `schema` | dict | Yes | - | Key-description dictionary of target fields |
| `model` | string | No | `"qwen2.5:1.5b"` | Local LLM model tag |
| `base_url` | string | No | `"http://localhost:11434"` | Ollama service base URL |

**Example in `flow.md` (Markdown):**
```markdown
### step_extract_invoice. Extract Invoice Data (`ai.extract`)
- **output_var:** `invoice`
- **text:** ${ocr_text}
- **schema:** {"invoice_number": "Invoice identifier number", "total_amount": "Total due as float number", "due_date": "Due date in YYYY-MM-DD"}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_extract_invoice",
  "name": "Extract Invoice Data",
  "action": "ai.extract",
  "parameters": {
    "text": "${ocr_text}",
    "schema": {
      "invoice_number": "Invoice identifier number",
      "total_amount": "Total due as float number",
      "due_date": "Due date in YYYY-MM-DD"
    }
  },
  "output_var": "invoice"
}
```

---

### `ai.decide`
Executes rapid, zero-hallucination semantic decisions, intent classification, priority scoring, or boolean validations using **OpenThai-SystemOne** (0.8B) in a single forward pass (<50ms).

**Parameters:**
| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `state` | string / dict | Yes | - | Input context, user message, or record data |
| `question` | dict | Optional | - | Single decision question definition (see below) |
| `questions` | dict | Optional | - | Multi-question dictionary |
| `base_url` | string | No | `"http://localhost:8000"` | OpenThai-SystemOne API base URL |
| `timeout` | number | No | `30` | Request timeout in seconds |
| `fallback_to_ollama` | boolean | No | `true` | Fallback to local Ollama if SystemOne server is offline |

**Question Object Properties:**
* **`type`**: `"choice"` (pick one from list), `"score"` (rate 1-5 or 1-10), or `"noul"` (yes/no).
* **`instructions`**: Guidance string describing what decision to make.
* **`options`**: List of string options (for `choice` type). Automatically converted to criteria.
* **`criteria`**: Key-value mapping of option names to descriptions (or `null`).

**Example (Intent Classification) in `flow.md` (Markdown):**
```markdown
### step_classify_inquiry. Route Customer Inquiry (`ai.decide`)
- **output_var:** `route_decision`
- **state:** ${email.body}
- **question:** {"name": "intent", "type": "choice", "instructions": "ระบุเจตนาหลักของอีเมลฉบับนี้", "options": ["ขอใบเสร็จรับเงิน", "แจ้งปัญหาการใช้งาน", "สอบถามราคา", "ยกเลิกบริการ"]}
```

**Compiled `flow.json`:**
```json
{
  "id": "step_classify_inquiry",
  "name": "Route Customer Inquiry",
  "action": "ai.decide",
  "parameters": {
    "state": "${email.body}",
    "question": {
      "name": "intent",
      "type": "choice",
      "instructions": "ระบุเจตนาหลักของอีเมลฉบับนี้",
      "options": ["ขอใบเสร็จรับเงิน", "แจ้งปัญหาการใช้งาน", "สอบถามราคา", "ยกเลิกบริการ"]
    }
  },
  "output_var": "route_decision"
}
```

**Output Format:**
```json
{
  "choice": "ขอใบเสร็จรับเงิน",
  "confidence": 0.94,
  "probabilities": {
    "ขอใบเสร็จรับเงิน": 0.94,
    "แจ้งปัญหาการใช้งาน": 0.03,
    "สอบถามราคา": 0.02,
    "ยกเลิกบริการ": 0.01
  },
  "type": "choice",
  "model": "openthai-systemone"
}
```

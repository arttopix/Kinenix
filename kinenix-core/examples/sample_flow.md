# Sample Kinenix Flow
> Description: Test flow executing variables, logic, delay, and HTTP API actions
> Version: 1.0.0

## Variables
- `welcome_msg`: Hello Kinenix
- `target_url`: https://httpbin.org/get

## Steps

### 1. Set Initial Variable (`logic.set_variable`)
- **output_var:** `set_result`
- **name:** status_flag
- **value:** active

### 2. Short Delay (`logic.delay`)
- **seconds:** 0.5

### 3. Execute HTTP GET Request (`http.request`)
- **output_var:** `api_response`
- **url:** ${target_url}
- **method:** GET

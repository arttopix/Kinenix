# Hello Kinenix
> Description: A first flow that builds a small greeting table from config.json and writes it to a CSV file. It needs no browser and no internet.
> Version: 1.0.0

## Variables
- `greetings`: []

## Steps

### 1. Build One Greeting Per Name (`logic.loop`)
- **items:** `${config.names}`
- **item_var:** `name`
- **Sub-steps:**
  - Add Greeting Row (`logic.append`):
    - **target:** `greetings`
    - **item:** {"Name": "${name}", "Greeting": "${config.greeting}, ${name}!"}

### 2. Stop When There Is Nobody To Greet (`flow.fail`)
- **condition:** `${greetings} == []`
- **message:** config.json has no names to greet; add some to "names"

### 3. Write Greetings To CSV (`csv.write`)
- **file_path:** `${config.output_path}`
- **data:** `${greetings}`
- **columns:** ["Name", "Greeting"]
- **output_var:** `csv_result`

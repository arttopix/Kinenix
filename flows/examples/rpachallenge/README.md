# RPA Challenge Solver

Solves the classic [RPA Challenge](https://rpachallenge.com/): it reads `assets/challenge.xlsx`, then fills the web form ten times while the form fields move around. It also collects the people who are not programmers into a list.

Needs a browser and internet access. Install the browser once with `kinenix install-browsers`.

```bash
kinenix run .
```

A browser window opens (set `headless` in `flow.md` step 1 to `true` to hide it, for example on a server). When it finishes, the challenge's result message is saved as a screenshot in `output/screenshots/`.

## How it works

| Step | What it does |
| :--- | :--- |
| 1-3 | Opens the site, reads the Excel file, and starts the timer |
| 4 | For each row, fills the form by its labels, which keeps working when the fields move; rows with a role other than Programmer are also added to a list |
| 5-6 | Saves a screenshot of the result and closes the browser |
| 7 | Optionally emails the result (off by default) |

## Configuration (`config/config.json`)

| Key | Purpose |
| :--- | :--- |
| `website` | The challenge URL |
| `excel_path` | Input data, relative to this folder |
| `screenshot_path`, `error_dir` | Result screenshot and automatic failure screenshots |
| `send_notification` | `true` runs step 7, which needs the shared `@shared/send_email.json` subflow from the Kinenix repository |
| `email_to`, `email_subject`, `dry_run` | Email settings for step 7 |

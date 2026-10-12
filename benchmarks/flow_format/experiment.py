"""Ask a local model to write bot_fx_rate in Markdown and in YAML from the same requirement; score both.

Results and method: docs/benchmarks/flow_format.md. Run from this folder with Ollama running:
    pip install requests pyyaml          (PyYAML is needed only for this benchmark, not by Kinenix)
    kinenix actions > actions.txt        (refresh the action list for the prompt)
    python experiment.py qwen2.5-coder:7b 5 --machine laptop-rtx3050ti
    python experiment.py --rescore       (score every saved flow again with the installed Kinenix, print the table)

Both prompts carry the same requirement, config keys, action list, and rules; only the format
description and the example differ (same example flow in each format).
"""
import argparse
import json
import re
import socket
import statistics
import time
from pathlib import Path

import requests

from kinenix.engine.markdown import markdown_issues, markdown_to_flow
from kinenix.engine.validation import validate_flow
from yaml_flow import yaml_to_flow

HERE = Path(__file__).parent
RESULTS = HERE / "results"

REQUIREMENT = """Goal: collect Bank of Thailand buying transfer rates for several currencies over one month and email them as a CSV file.
Steps:
1. Work out the first and last day of the report month (config.month: {"date": "today", "add_months": -1}).
2. Open ${config.url}; accept the cookie banner if it appears (button text 'Accept recommended cookies').
3. Open the currency filter (#dropdownCurrency) and tick each currency in ${config.currencies}
   (checkbox: .currency-filter input[name='currencyCheck'][value='<currency>']).
4. Pick the start and end dates in the date picker: year select is '.react-datepicker select >> nth=1',
   month select (by month name) is '.react-datepicker select >> nth=0', day cell text is the day number.
5. Click 'button.historical-btn' to search.
6. For each currency, click its tab button (text = currency) and read the visible table: keep columns
   "Period" as "Date" and "Buying Rates Transfer" as "Buying Transfer Rate" (a number), add a Currency column.
7. Write all rows to ${config.output_path} with columns Currency, Date, Buying Transfer Rate.
8. Close the browser and email the CSV to ${config.email.to} (subject ${config.email.subject}).
Errors: retry opening the page and searching twice; retry writing the CSV twice; the screenshot may fail.
Config keys: url, currencies, month.date, month.add_months, output_path, headless, email.to, email.subject, email.body, email.dry_run."""

RULES = """Rules: use only the actions listed, with only their parameters. Store a result with output_var and
use it later as ${name}, fields as ${name.field}. A loop uses logic.loop with items and item_var, and its
steps run once per item. Error handling per step: on_error (retry or continue), max_retries, retry_interval.
Reply with the flow file only, no explanation."""

MD_FORMAT = """Format: Markdown (flow.md).
# <Flow name>
> Description: <one line>

## Variables
- `name`: <initial value>

## Steps

### <number>. <Step name> (`<action>`)
- **<parameter>:** <value>
- **output_var:** `<name>`
- **on_error:** retry
- **max_retries:** 2
- **Sub-steps:**            (only for logic.loop; indent the sub-steps by 2 spaces)
  - <Sub-step name> (`<action>`):
    - **<parameter>:** <value>

Example:
# Greet Names

## Variables
- `rows`: []

## Steps

### 1. Each Name (`logic.loop`)
- **items:** `${config.names}`
- **item_var:** `n`
- **Sub-steps:**
  - Add Row (`logic.append`):
    - **target:** rows
    - **item:** {"Name": "${n}"}

### 2. Save (`csv.write`)
- **file_path:** ./output/names.csv
- **data:** `${rows}`
- **on_error:** retry
- **max_retries:** 2
"""

YAML_FORMAT = """Format: YAML (flow.yaml).
name: <Flow name>
description: <one line>
variables:
  <name>: <initial value>
steps:
  - name: <Step name>
    action: <action>
    with:                     (the action's parameters)
      <parameter>: <value>
    output_var: <name>
    on_error: retry
    max_retries: 2
    steps:                    (only for logic.loop: the steps that run per item)
      - name: <Sub-step name>
        action: <action>
        with:
          <parameter>: <value>
Quote values that start with #, [, {, * or contain ": ".

Example:
name: Greet Names
variables:
  rows: []
steps:
  - name: Each Name
    action: logic.loop
    with:
      items: ${config.names}
      item_var: n
    steps:
      - name: Add Row
        action: logic.append
        with:
          target: rows
          item: {"Name": "${n}"}
  - name: Save
    action: csv.write
    with:
      file_path: ./output/names.csv
      data: ${rows}
    on_error: retry
    max_retries: 2
"""

EXPECTED_ACTIONS = {"date.calc", "web.open", "web.click", "web.check", "web.select_option", "logic.loop",
                    "web.get_table", "logic.append", "csv.write", "web.close", "email.send"}


def ask(model, prompt):
    for attempt in range(5):
        try:
            return _ask(model, prompt)
        except requests.exceptions.ConnectionError:
            time.sleep(10)
    return _ask(model, prompt)


def _ask(model, prompt):
    started = time.time()
    r = requests.post("http://127.0.0.1:11434/api/generate", json={
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.7, "num_ctx": 8192, "num_predict": 3000}}, timeout=900)
    r.raise_for_status()
    return r.json()["response"], time.time() - started


def strip_fence(text):
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    return m.group(1) if m else text


def walk(steps):
    for s in steps:
        yield s
        yield from walk(s.sub_steps or [])
        yield from walk(s.else_steps or [])


def score(kind, text):
    body = strip_fence(text)
    result = {"parsed": False, "steps": 0, "problems": None, "actions_covered": 0, "error": None}
    try:
        if kind == "md":
            flow = markdown_to_flow(body)
            problems = markdown_issues(body)
        else:
            problems = []
            flow = yaml_to_flow(body, problems)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
        return result
    steps = list(walk(flow.steps))
    result["parsed"] = bool(flow.steps)
    result["steps"] = len(steps)
    result["problems"] = len(problems) + len(validate_flow(flow))
    result["actions_covered"] = len(EXPECTED_ACTIONS & {s.action for s in steps})
    result["has_loop_substeps"] = any(s.action == "logic.loop" and s.sub_steps for s in steps)
    return result


def generate(model, runs, machine):
    out = RESULTS / machine / model.replace(":", "_")
    out.mkdir(parents=True, exist_ok=True)
    actions = (HERE / "actions.txt").read_text(encoding="utf-8")
    common = (f"You write automation flows for Kinenix.\n\nRequirement:\n{REQUIREMENT}\n\n"
              f"Actions and their parameters:\n{actions}\n{RULES}\n\n")
    scores = []
    for run in range(1, runs + 1):
        for kind, fmt in (("md", MD_FORMAT), ("yaml", YAML_FORMAT)):
            text, seconds = ask(model, common + fmt + "\nNow write the flow for the requirement.")
            (out / f"run{run}.{kind}").write_text(text, encoding="utf-8")
            res = score(kind, text)
            res.update(run=run, kind=kind, seconds=round(seconds))
            scores.append(res)
            print(json.dumps(res, ensure_ascii=False), flush=True)
    (out / "scores.jsonl").write_text("".join(json.dumps(r) + "\n" for r in scores), encoding="utf-8")


def rescore():
    """Scores every saved flow again with the installed Kinenix; generation time is kept from the run."""
    for scores_file in sorted(RESULTS.glob("*/*/scores.jsonl")):
        old = {(r["run"], r["kind"]): r for r in map(json.loads, scores_file.read_text(encoding="utf-8").splitlines())}
        new = []
        for (run, kind), previous in sorted(old.items()):
            res = score(kind, (scores_file.parent / f"run{run}.{kind}").read_text(encoding="utf-8"))
            res.update(run=run, kind=kind, seconds=previous["seconds"])
            new.append(res)
        scores_file.write_text("".join(json.dumps(r) + "\n" for r in new), encoding="utf-8")


def table():
    print("| Machine | Model | Format | Runs | Parsed | Clean | Loop with sub-steps | Actions (of 11) | Seconds per flow |")
    print("| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for scores_file in sorted(RESULTS.glob("*/*/scores.jsonl")):
        rows = [json.loads(line) for line in scores_file.read_text(encoding="utf-8").splitlines()]
        machine, model = scores_file.parent.parent.name, scores_file.parent.name
        for kind, label in (("md", "flow.md"), ("yaml", "YAML")):
            r = [x for x in rows if x["kind"] == kind]
            parsed = [x for x in r if x["parsed"]]
            print(f"| {machine} | {model} | {label} | {len(r)} | {len(parsed)} | "
                  f"{sum(1 for x in parsed if x['problems'] == 0)} | {sum(1 for x in parsed if x.get('has_loop_substeps'))} | "
                  f"{statistics.mean(x['actions_covered'] for x in r):.1f} | {statistics.mean(x['seconds'] for x in r):.0f} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model", nargs="?", help="Ollama model, for example qwen2.5-coder:3b")
    parser.add_argument("runs", nargs="?", type=int, default=5, help="Runs per format (default 5)")
    parser.add_argument("--machine", default=socket.gethostname().lower(),
                        help="Folder name for this machine's results (default: host name)")
    parser.add_argument("--rescore", action="store_true", help="Score all saved flows again, then print the table")
    args = parser.parse_args()
    if args.rescore:
        rescore()
    elif args.model:
        generate(args.model, args.runs, args.machine)
    else:
        parser.error("give a model, or --rescore")
    table()


if __name__ == "__main__":
    main()

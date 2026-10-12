# Flow Markdown Specification (`flow.md` Rulebook)

This document establishes the official syntax rules and structural guidelines for **`flow.md`**, the file format of every Kinenix flow.

---

## 1. Vision & Core Principles

A Kinenix flow is one file, **`flow.md`**: the file people read, the file an AI assistant writes, and the file Kinenix runs.

- **Readable:** Markdown with headings and bullet points, readable on GitHub, in an editor, or in a pull request diff.
- **Written well by AI:** the step headings and `- **parameter:** value` bullets are easy for language models to produce. In a comparison on the `bot_fx_rate` requirement, a local 7B model wrote valid `flow.md` more reliably than the same flow in YAML, whose quoting rules clash with `${...}` expressions ([benchmark](benchmarks/flow_format.md)).
- **Checked before it runs:** `kinenix validate`, `kinenix run`, and the worker parse the file, then report unknown actions and parameters, lines the parser ignores, and step headings without an action, with line numbers and suggestions.

There is no separate JSON file to keep in sync. `kinenix run` and `kinenix-worker run` read `flow.md` directly and compile it in memory on every run; subflows (`flow.call`) work the same way. To inspect the compiled form, run `kinenix compile <bundle>`, which prints it as JSON (validated against [flow.schema.json](../schemas/flow.schema.json)) without writing any file next to `flow.md`.

Flows written as `flow.json` by Kinenix 0.2.0b3 or older are not run; `kinenix export-md <bundle>` converts one into `flow.md` once. Files with a UTF-8 BOM (written by Windows PowerShell 5 and some editors) are read correctly.

---

## 2. The 5 Golden Rules of `flow.md`

To ensure 100% deterministic compilation without requiring massive cloud LLMs, every `flow.md` must strictly adhere to the following 5 rules:

```text
Rule 1: Document Header & Metadata (Title, Description, Variables)
Rule 2: Step Declarations with Mandatory Action Anchors in Parentheses
Rule 3: Key-Value Action Parameters as Bullet Points
Rule 4: Standard Indentation for Nested Sub-steps (Loops & Conditions)
Rule 5: Variable Interpolation Syntax (${config.*}, ${var.*})
```

---

### Rule 1: Document Header & Metadata

Every `flow.md` must start with a Level 1 Heading (`#`) denoting the Flow Name, followed by optional blockquotes for description and version, and an optional `## Variables` section.

#### Syntax
```markdown
# [Flow Name]
> Description: [Brief summary of business intent]
> Version: [Semantic version, e.g. 1.0.0]

## Variables
- `variable_name`: [initial_value]
```

#### Example
```markdown
# RPA Challenge Solver
> Description: Automatically complete 10 rounds of RPA Challenge form submission using Excel data.
> Version: 1.0.0

## Variables
- `non_programmers`: []
- `processed_count`: 0
```

---

### Rule 2: Step Declarations & Mandatory Action Anchors

Each step must be declared as a Level 3 Heading (`###`) and **MUST** include the exact registered action name in parentheses `([action_name])`.

#### Syntax
```markdown
### [Step Number or ID]. [Step Name] (`[action.name]`)
```

- **Step Number / ID:** Can be a number (`1.`) or explicit ID (`step_1.`). If a number is given, the compiler automatically assigns `step_1`, `step_2`, etc.
- **Action Anchor:** The action name enclosed in parentheses (e.g. `(web.open)`, `(excel.read)`, `(logic.loop)`). This anchor prevents AI models from inventing unregistered action names.

#### Example
```markdown
### 1. Open Challenge Webpage (`web.open`)
### 2. Read Candidate Spreadsheet (`excel.read`)
### 3. Click Start Timer Button (`web.click`)
```

---

### Rule 3: Key-Value Action Parameters as Bullet Points

All parameters passed to the action must be written as Markdown bullet items directly under the step header, using the format `- **parameter_name:** value`.

#### Syntax
```markdown
### [Step Name] (`[action.name]`)
- **[parameter_1]:** [value]
- **[parameter_2]:** [value]
- **output_var:** [variable_name]
```

#### Supported Value Types:
- **String:** `- **url:** https://example.com`
- **Boolean:** `- **headless:** false` or `- **clean_headers:** true`
- **Number:** `- **timeout:** 5000` or `- **delay:** 1.5`
- **Dynamic Variable Expression:** `- **url:** ${config.website}`
- **Output Variable:** `- **output_var:** my_result` (stores action result in context)
- **Error Handling:** `- **on_error:** retry`, `- **max_retries:** 2`, `- **retry_interval:** 3.0`, `- **fallback_step_id:** step_9`. These four keys are compiled into the step's `error_handler`, not into the action parameters (see [Step Resilience & Error Handling](actions_reference.md#step-resilience--error-handling-error_handler)).

#### Example
```markdown
### 1. Open Challenge Webpage (`web.open`)
- **url:** `${config.website}`
- **headless:** false
- **timeout:** 10000

### 2. Read Candidate Spreadsheet (`excel.read`)
- **file_path:** `${config.excel_path}`
- **clean_headers:** true
- **output_var:** `challenge_data`
```

---

#### Multi-line Values
A value with several lines, such as an email body, starts with `|` after the parameter name. The lines below it that are indented further than the parameter line are its value; their common indentation is removed, and blank lines inside are kept. The value ends at the first line that is not indented further, such as the next parameter.

```markdown
### 5. Email Report (`email.send`)
- **to:** `${config.email.to}`
- **subject:** Insurance packages
- **body:** |
    Hello,

    The packages for ${request_count} requests are attached.
    - Source: tipinsure.com
- **attachments:** ["${packed.zip_path}"]
```

The `body` above is `"Hello,\n\nThe packages for ${request_count} requests are attached.\n- Source: tipinsure.com"`. A `|` with no indented lines after it is the plain value `|` (for example `- **delimiter:** |`). Text lines under a step that are neither a parameter nor part of a `|` value are ignored, and `kinenix validate` reports each one with its line number.

---

### Rule 4: Standard Indentation for Control Flow (`logic.loop` & `logic.if`)

For actions that contain nested steps, use standard Markdown 2-space or 4-space indentation under `- **Sub-steps:**` (and optionally `- **Else-steps:**` for `logic.if`).

#### A. Loop Syntax (`logic.loop`)
```markdown
### [Step Name] (`logic.loop`)
- **items:** `${collection_variable}`
- **item_var:** `item_name`
- **Sub-steps:**
  - [Child Step Name] (`[action.name]`):
    - **param1:** value
    - **param2:** value
```

#### B. Condition Syntax (`logic.if`)
```markdown
### [Step Name] (`logic.if`)
- **condition:** `${row.Status} == 'Active'`
- **Sub-steps:**
  - [Then Step Name] (`[action.name]`):
    - **param1:** value
- **Else-steps:**
  - [Else Step Name] (`[action.name]`):
    - **param1:** value
```


#### C. Conditions
`condition` on any step runs the step only when the condition is true; on `logic.if` it chooses between `Sub-steps` and `Else-steps`. A condition is `left operator right`, or `left is empty` / `left is not empty`:

| Operator | True when |
| :--- | :--- |
| `==`, `!=` | the two sides are equal / differ (text comparison ignores case) |
| `>`, `>=`, `<`, `<=` | both sides are numbers and compare so |
| `contains`, `not contains` | right is / is not part of left; with a list on the left, an item equals right |
| `in`, `not in` | left is / is not part of right; with a list on the right, an item equals left |
| `starts with`, `ends with` | left starts / ends with right |
| `is empty`, `is not empty` | left is / is not missing or blank (no right side) |

The condition is split into its sides before variables are replaced, so values containing `<`, `>`, or the word `in` (for example `< 5,000 km`) never split it, and neither does text inside `${...}` or quotes. Quote a literal that contains an operator: `${label} == 'x > y'`.

```markdown
### 6. Skip Requests Without A Model (`flow.fail`)
- **condition:** `${req.model} is empty`
- **message:** Request ${req.request_id} has no car model
- **category:** business
```

#### Example
```markdown
### 4. Loop Applicants and Submit Form (`logic.loop`)
- **items:** `${challenge_data}`
- **item_var:** `row`
- **Sub-steps:**
  - Fill First Name (`web.type`):
    - **selector:** `//input[@ng-reflect-name="labelFirstName"]`
    - **text:** `${row.First Name}`
  - Fill Last Name (`web.type`):
    - **selector:** `//input[@ng-reflect-name="labelLastName"]`
    - **text:** `${row.Last Name}`
  - Click Round Submit Button (`web.click`):
    - **selector:** `input[value="Submit"]`
```

---

### Rule 5: Variable Interpolation Syntax

Dynamic variables must use the standard expression format:

- **`${config.property}`**: Accesses configuration values loaded from `config/config.json`.
- **`${variable_name}`**: Accesses runtime variables initialized in flow or stored by `output_var`.
- **`${item.property}`**: Accesses fields of the current iteration object in `logic.loop`.
- **`${env.VAR_NAME}`**: Accesses operating system environment variables.
- **`${__flow_dir__}`**: The absolute path of the flow's bundle folder. Relative paths in file actions already resolve against it; use it to build an absolute path, for example to pass a file location to a subflow: `"${__flow_dir__}/output/report.csv"`.

---

## 3. Complete Reference Example

Below is the complete `flow.md` specification for the **RPA Challenge Solver** benchmark:

```markdown
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
    - **condition:** `${row.Role in Company} == 'Programmer'`
    - **Sub-steps:**
      - Fill First Name (`web.type`):
        - **selector:** `//input[@ng-reflect-name="labelFirstName"]`
        - **text:** `${row.First Name}`
      - Fill Last Name (`web.type`):
        - **selector:** `//input[@ng-reflect-name="labelLastName"]`
        - **text:** `${row.Last Name}`
    - **Else-steps:**
      - Record Non-Programmer Person (`logic.append`):
        - **target:** non_programmers
        - **item:** `{"First Name": "${row.First Name}", "Role in Company": "${row.Role in Company}"}`
  - Click Round Submit Button (`web.click`):
    - **selector:** `input[value="Submit"]`

### 5. Take Screenshot of Result (`web.screenshot`)
- **path:** `${config.screenshot_path}`

### 6. Close Browser (`web.close`)
```

---

## 4. Checking and Inspecting a Flow

1. **Validation of actions and parameters:**
   ```bash
   kinenix validate flows/examples/rpachallenge          # exit code 1 when problems are found
   ```
   Each action declares the parameters it reads. `kinenix validate`, `kinenix run`, and `kinenix-worker run` report unknown actions, parameters that no action reads (which would otherwise be ignored silently), lines the parser ignores, step headings without an action, and a flow without steps, and suggest the closest name (for example `timout` -> `timeout`). They also follow `flow.call` targets into subflows. `run` only warns, except that a flow without steps does not run. The `kinenix-core` test suite validates every flow under `flows/` and every example in `docs/`.
2. **Compiled form (for inspection):**
   ```bash
   kinenix compile flows/examples/rpachallenge                     # print the compiled flow as JSON
   kinenix compile flows/examples/rpachallenge -o /tmp/flow.json   # or write it to a file
   kinenix compile flows/examples/rpachallenge --strict            # also exit 1 when validation finds problems
   ```
   The result is validated against `kinenix.models.flow.FlowDefinition`; parsing errors name the line.
3. **Converting an old JSON flow (once):**
   ```bash
   kinenix export-md path/to/old_bundle      # writes flow.md next to the old flow.json
   ```

---

## 5. AI Prompting Template for Generating `flow.md`

When prompting an LLM or Small Language Model (SLM) to generate a new workflow, provide this system prompt:

```text
You are an expert RPA workflow architect for kinenix.
Generate a valid flow specification adhering strictly to the Flow Markdown Specification rules:
1. Title with Level 1 Heading (# Flow Name).
2. Level 3 Heading for each step with explicit action anchor: ### Step Name (`action.name`).
3. Parameters formatted as bullet points: - **param_name:** value.
4. Output variable formatted as: - **output_var:** var_name.
5. Indented sub-steps under - **Sub-steps:** for loops and conditions.
Only output the raw Markdown content.
```

# Flow Markdown Specification (`flow.md` Rulebook)

This document establishes the official syntax rules, structural guidelines, and compilation contracts for **`flow.md`** files within **kinenix**.

---

## 1. Vision & Core Principles

In kinenix, automation workflows maintain a **Dual-Representation Lifecycle**:

1. **`flow.md` (Specification & Living Blueprint):**
   - High-level, human-readable, and AI-native authoring format.
   - Designed for easy reading by business analysts, developers, and Large Language Models (LLMs).
   - Clean Git diffs and straightforward pull request reviews.
2. **`flow.json` (Runtime Execution Contract):**
   - Strict, deterministic JSON schema validated by Pydantic v2.
   - Directly executed by `kinenix-core` and `kinenix-worker` with zero runtime parsing overhead.

> **Compilation Principle:** `flow.md` is compiled ahead-of-time (AOT) into `flow.json`. The execution runtime (`kinenix-core` and `kinenix-worker`) strictly executes `flow.json` to guarantee sub-millisecond execution speeds, zero hallucination, and pre-flight validation.

### Source of Truth

In a bundle that has a `flow.md`, **`flow.md` is the only file you edit**. `flow.json` is its build output: it stays in git so Studio, workers, and schema tools can read it, but it is never edited by hand.

Before every run, `kinenix run` and `kinenix-worker run` compare the two files by content (not by timestamp, because `git checkout` resets timestamps):

| Situation | What happens |
| :--- | :--- |
| `flow.json` missing | Compiled from `flow.md`, then run |
| Same content | Runs `flow.json` |
| `flow.md` changed after `flow.json` | `flow.json` is recompiled, then run |
| `flow.json` changed after `flow.md` (e.g. edited in Studio) | A warning is shown and `flow.json` runs unchanged, so the edit is not lost. Keep it with `kinenix export-md <bundle>` (regenerates `flow.md`, losing hand formatting) or discard it with `kinenix compile <bundle>` |

The `kinenix-core` test suite also checks that every committed `flow.json` under `flows/` matches its `flow.md`, so CI fails when a compile was forgotten. Files with a UTF-8 BOM (written by Windows PowerShell 5 and some editors) are read correctly.

Studio currently saves to `flow.json` only, which triggers the warning above until the bundle is exported or recompiled.

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

#### Example
```markdown
### 4. Loop Applicants and Submit Form (`logic.loop`)
- **items:** `${challenge_data}`
- **item_var:** `row`
- **Sub-steps:**
  - Fill First Name (`web.type`):
    - **selector:** `//input[@ng-reflect-name="labelFirstName"]`
    - **value:** `${row.First Name}`
  - Fill Last Name (`web.type`):
    - **selector:** `//input[@ng-reflect-name="labelLastName"]`
    - **value:** `${row.Last Name}`
  - Click Round Submit Button (`web.click`):
    - **selector:** `input[value="Submit"]`
```

---

### Rule 5: Variable Interpolation Syntax

Dynamic variables in both `flow.md` and `flow.json` must strictly use the standard expression format:

- **`${config.property}`**: Accesses configuration values loaded from `config/config.json`.
- **`${variable_name}`**: Accesses runtime variables initialized in flow or stored by `output_var`.
- **`${item.property}`**: Accesses fields of the current iteration object in `logic.loop`.
- **`${env.VAR_NAME}`**: Accesses operating system environment variables.

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
        - **value:** `${row.First Name}`
      - Fill Last Name (`web.type`):
        - **selector:** `//input[@ng-reflect-name="labelLastName"]`
        - **value:** `${row.Last Name}`
    - **Else-steps:**
      - Record Non-Programmer Person (`logic.append`):
        - **target_list:** `${non_programmers}`
        - **item:** `{"First Name": "${row.First Name}", "Role in Company": "${row.Role in Company}"}`
  - Click Round Submit Button (`web.click`):
    - **selector:** `input[value="Submit"]`

### 5. Take Screenshot of Result (`web.screenshot`)
- **path:** `${config.screenshot_path}`

### 6. Close Browser (`web.close`)
```

---

## 4. Compilation Contract & Validation

1. **Compilation Command (CLI):**
   ```bash
   kinenix compile flows/examples/rpachallenge/flow.md
   ```
2. **Reverse Export Command (CLI):**
   ```bash
   kinenix export-md flows/examples/rpachallenge/flow.json
   ```
3. **Validation of Actions and Parameters:**
   ```bash
   kinenix validate flows/examples/rpachallenge          # exit code 1 when problems are found
   kinenix compile flows/examples/rpachallenge --strict  # compile, then fail on problems (for CI)
   ```
   Each action declares the parameters it reads. `kinenix validate`, `kinenix compile`, `kinenix run`, and `kinenix-worker run` report unknown actions and parameters that no action reads, which would otherwise be ignored silently, and suggest the closest name (for example `timout` -> `timeout`). `compile` and `run` only warn. The `kinenix-core` test suite validates every flow under `flows/`.
4. **Pydantic Validation Guarantee:**
   During compilation, the resulting dictionary is validated against `kinenix.models.flow.FlowDefinition`.
   - If validation succeeds, `flow.json` is generated or overwritten atomically.
   - If validation fails, exact error line numbers and missing fields are reported, and existing `flow.json` is left untouched.

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

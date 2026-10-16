# Hello Kinenix

The smallest useful flow: it reads a list of names from `config/config.json`, builds one greeting per name with a subflow, and writes them to `output/greetings.csv`. It needs no browser and no internet, so it is the quickest way to check an installation.

```bash
kinenix run .
```

Open `output/greetings.csv`:

```csv
Name,Greeting
Somchai,"Hello, Somchai!"
Malee,"Hello, Malee!"
Alex,"Hello, Alex!"
```

## Try changing it

- **Change the data:** edit `names` or `greeting` in `config/config.json` and run again. The flow itself does not change.
- **Change the flow:** edit `flow.md`, for example add a column to the row in step 1.
- **Change the subflow:** `subflows/make_greeting.md` builds one row. Add a field to its `value`, and add the column to `columns` in step 3 of `flow.md`.
- **See an error handled:** set `"names": []`. Step 2 stops the flow with a clear business message instead of writing an empty file.

## Files

| File | Purpose |
| :--- | :--- |
| `flow.md` | The flow, written in Markdown. This is the file you edit. |
| `config/config.json` | Values the flow reads as `${config.*}`. |
| `subflows/make_greeting.md` | A subflow: `flow.md` calls it for each name with `flow.call`. |
| `output/` | Created when the flow runs. |

## How the subflow works

```markdown
  - Make Greeting (`flow.call`):
    - **flow:** ./subflows/make_greeting.md
    - **inputs:** {"name": "${name}"}
    - **output_var:** `row`
```

- `flow` points at the subflow's `.md` file. It is compiled when the flow runs; no `.json` file is needed next to it.
- `inputs` passes values to the subflow; it declares them in its own `## Variables` (`name`). `kinenix validate` reports an input the subflow does not declare.
- A subflow inside the bundle sees the bundle's `${config.*}` (here `greeting`), and its relative paths resolve against the bundle folder, as in `flow.md`.
- `flow.return` sends a value back; `output_var` stores it (`row`).

Subflows shared by many projects live in `@shared/` and keep their own config; pass values with `inputs`, or the caller's whole config with `inherit_config: true` (see the project bundles guide).

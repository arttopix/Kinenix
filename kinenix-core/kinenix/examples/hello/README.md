# Hello Kinenix

The smallest useful flow: it reads a list of names from `config/config.json`, builds one greeting per name, and writes them to `output/greetings.csv`. It needs no browser and no internet, so it is the quickest way to check an installation.

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
- **Change the flow:** edit `flow.md` (the source; `flow.json` is rebuilt from it on the next run), for example add a column to the row in step 1.
- **See an error handled:** set `"names": []`. Step 2 stops the flow with a clear business message instead of writing an empty file.

## Files

| File | Purpose |
| :--- | :--- |
| `flow.md` | The flow, written in Markdown. This is the file you edit. |
| `flow.json` | Build output of `flow.md`; do not edit it by hand. |
| `config/config.json` | Values the flow reads as `${config.*}`. |
| `output/` | Created when the flow runs. |

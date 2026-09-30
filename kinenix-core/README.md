# kinenix

Core execution engine and `kinenix` CLI for **Kinenix**, an open-source, local AI-native RPA framework in Python.

> **Status: beta.** Flow schemas and action parameters may still change between releases.

- Runs automation flows written as `flow.json` or `flow.md`
- Built-in actions for web automation (Playwright), Excel and CSV (no Microsoft Office required), files, HTTP, email, and flow control
- Local AI actions through Ollama, so business data stays on your machine
- Retries, fallbacks, failure screenshots, and structured JSON execution logs

## Installation

```bash
pip install kinenix
kinenix install-browsers   # Playwright Chromium, needed for web actions
kinenix --version
```

Requires Python 3.10 or newer.

## Usage

```bash
kinenix list                       # list flows found in the current project
kinenix run path/to/flow.json      # run a flow
kinenix compile path/to/flow.md    # compile flow.md into flow.json
kinenix version                    # version and environment details
```

## Related packages

The worker, Studio, and Orchestrator modules live in the same repository and are not yet published on PyPI.

## Documentation

- [Project README](https://github.com/arttopix/Kinenix#readme)
- [Actions reference](https://github.com/arttopix/Kinenix/blob/main/docs/actions_reference.md)
- [Flow Markdown specification](https://github.com/arttopix/Kinenix/blob/main/docs/flow_markdown_spec.md)
- [CLI guide](https://github.com/arttopix/Kinenix/blob/main/docs/cli_guide.md)

## License

MIT

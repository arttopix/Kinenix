# {{title}}

A [Kinenix](https://github.com/arttopix/Kinenix) automation project.

## How to build it

1. **Describe the task** in `requirements.md`: goal, steps, settings that must be changeable, output, errors, schedule.
2. **Let an AI assistant write the flow.** Open this folder in your assistant (for example Claude Code) and ask: "Build the flow described in requirements.md." It follows `AGENTS.md`, writes `flow.md`, and puts settings in `config/config.json`.
3. **Check and run it:**
   ```bash
   kinenix validate .
   kinenix run .
   ```
4. **Review** `flow.md` and the results in `output/`. Change settings in `config/config.json` without touching the flow.

To run it on a schedule, see the worker guide: https://github.com/arttopix/Kinenix/blob/main/kinenix-worker/README.md

## Files

| File | Purpose |
| :--- | :--- |
| `requirements.md` | What the automation must do. You write it. |
| `flow.md` | The flow. Written by you or an AI assistant from `requirements.md`. |
| `flow.json` | Build output of `flow.md`, rebuilt before each run. Do not edit. |
| `config/config.json` | Settings the flow reads as `${config.*}`. |
| `.env.example` | Names of the secrets the flow needs. Copy to `.env` and fill in; `.env` is never committed. |
| `AGENTS.md`, `CLAUDE.md` | Instructions for AI assistants working in this folder. |
| `output/` | Results, created when the flow runs. |

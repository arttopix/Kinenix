# Benchmark: Which Flow Format Do Local AI Models Write Best?

Date: 2026-10-12. Kinenix 0.2.0b3 (development branch). Scripts and every generated flow: [`benchmarks/flow_format/`](../../benchmarks/flow_format/).

## Summary

Kinenix flows are written by AI assistants from a requirement. We compared two formats for that file, Kinenix's `flow.md` and a YAML equivalent, by asking five small local models, from two model families and on two machines, to write the same flow in both formats.

- **`flow.md` was better for every model of 3B or more, on both machines.** For example, `qwen2.5-coder:7b` parsed 5 of 5 `flow.md` flows (9.2 of the 11 needed actions on average) against 2 of 5 in YAML, and `phi4-mini` parsed 9 of 10 against 3 of 10.
- Code-trained models write flows much better than general models of the same size: `qwen2.5-coder:3b` used 9.0 of the 11 actions, `qwen2.5:3b` 6.2.
- YAML broke on syntax, not on understanding: Kinenix's `${...}` expressions inside `[ ]`, unquoted `:` in selectors, and `#` at the start of a value.
- `flow.md` failures were silent before this test (a step heading without its action produced an empty flow with no warning). Kinenix now reports them.

Decision: Kinenix keeps `flow.md` as its only flow format, and drops `flow.json`.

For a small machine, `phi4-mini` (MIT license) is the best candidate found so far; `qwen2.5-coder:3b` scored higher but its license allows research use only (see [Models and licenses](#models-and-licenses)).

## Setup

| Machine | Hardware | Runtime | Models |
| :--- | :--- | :--- | :--- |
| `laptop-rtx3050ti` | Laptop, Intel Core i5-12500H, 16 GB RAM, NVIDIA RTX 3050 Ti Laptop GPU (4 GB VRAM), Windows 11 | Ollama 0.40.3 (CUDA) | `qwen2.5:1.5b`, `qwen2.5:3b`, `qwen2.5-coder:7b` |
| `ubuntu-rx550` | Desktop, Intel Core i5-3570 (2012, no AVX2), 7.7 GB RAM, AMD Radeon 540/550 (Lexa, about 4 GB VRAM), Ubuntu 24.04 | Ollama 0.34.2 (Vulkan) | `qwen2.5-coder:3b`, `phi4-mini` |

All models are Ollama's default Q4_K_M quantization of the instruct (chat) variant. Settings: temperature 0.7, context 8192 tokens, up to 3000 output tokens. Runs: 10 per format, except 5 per format for `qwen2.5-coder:7b`, which does not fit in 4 GB of VRAM and took about 115 seconds per flow.

Generation speed depends on the machine and on whether the model fits in GPU memory; accuracy does not. `phi4-mini` with an 8192-token context needed 3.7 GB and ran 14% on the CPU (`ollama ps`), so its time per flow is slower than the model itself.

### Models and licenses

| Model | Family | Parameters | License |
| :--- | :--- | ---: | :--- |
| `qwen2.5:1.5b` | Qwen (Alibaba) | 1.5B | Apache 2.0 |
| `qwen2.5:3b` | Qwen (Alibaba) | 3.1B | Qwen Research License (non-commercial) |
| `qwen2.5-coder:3b` | Qwen (Alibaba) | 3.1B | Qwen Research License (non-commercial) |
| `phi4-mini` | Phi (Microsoft) | 3.8B | MIT |
| `qwen2.5-coder:7b` | Qwen (Alibaba) | 7.6B | Apache 2.0 |

Licenses differ by size within one family; check the model card before using a model in production.

## Task

The flow is [`bot_fx_rate`](../../flows/examples/bot_fx_rate/): open the Bank of Thailand exchange rate page, pick currencies and a date range in a date picker, read one table per currency, write a CSV, and email it. It needs 11 different actions, two loops, and retries.

Each prompt contained, in this order:

1. The requirement, including the selectors to use and the config keys.
2. The list of Kinenix actions and their parameters (`kinenix actions`).
3. The same rules (use only listed actions, `output_var`, loops, error handling).
4. The format: a short description and **the same example flow** written in that format.

Only part 4 differed between the two formats. The YAML format puts action parameters under `with:` (as in GitHub Actions), because some parameter names (`name`, `condition`) would otherwise clash with step keys.

## Scoring

| Measure | Meaning |
| :--- | :--- |
| Parsed | The file was read without a syntax error and produced at least one step |
| Clean | Parsed, and `kinenix validate` (plus, for `flow.md`, the ignored-line check) reported no problem |
| Loop with sub-steps | At least one `logic.loop` has its sub-steps attached |
| Actions | How many of the 11 needed actions appear (average over all runs) |

These measure whether the file is usable as a starting point, not whether the flow would succeed against the live site. The saved flows can be scored again with a newer Kinenix (`--rescore`); the table below was rescored with the checks added after this test (step headings without an action, flows without steps) and did not change.

## Equivalence check

Before asking any model, `bot_fx_rate` was written by hand in YAML and read with a 40-line prototype reader. Both files produced the same 22 steps, and the YAML version ran against the live site: 42 executed steps, 110 rows for September 2026, 13.5 seconds. Both formats can express the flow; the question is which one models write correctly.

## Results

| Machine | Model | Format | Runs | Parsed | Clean | Loop with sub-steps | Actions (of 11) | Seconds per flow |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| laptop | qwen2.5 1.5B | flow.md | 10 | 5 | 0 | 0 | 3.2 | 17 |
| laptop | qwen2.5 1.5B | YAML | 10 | **7** | **2** | **1** | 2.4 | 14 |
| laptop | qwen2.5 3B | flow.md | 10 | **10** | 1 | 2 | **6.2** | 23 |
| laptop | qwen2.5 3B | YAML | 10 | 6 | **3** | **4** | 5.3 | 21 |
| ubuntu | qwen2.5-coder 3B | flow.md | 10 | **10** | 2 | **9** | **9.0** | 63 |
| ubuntu | qwen2.5-coder 3B | YAML | 10 | 2 | 2 | 2 | 1.9 | 57 |
| ubuntu | phi4-mini (3.8B) | flow.md | 10 | **9** | **4** | **9** | **7.3** | 110 |
| ubuntu | phi4-mini (3.8B) | YAML | 10 | 3 | 2 | 3 | 2.5 | 85 |
| laptop | qwen2.5-coder 7B | flow.md | 5 | **5** | 2 | **4** | **9.2** | 117 |
| laptop | qwen2.5-coder 7B | YAML | 5 | 2 | 2 | 2 | 3.8 | 112 |

The better format for each model and measure is in bold. Raw flows and per-run scores: `benchmarks/flow_format/results/<machine>/<model>/`.

## What went wrong

**`flow.md`**

- **Step heading without its action** (1.5B, 5 of 10 runs): `### 1. Open ${config_url}` followed by a `- **web.open**` bullet. The parser found no steps and, at the time, said nothing.
- **Sub-steps not indented as sub-steps** (3B, most runs): bullets under `- **Sub-steps:**` written as parameters or plain text.
- **Parameters an action does not accept** (7B): for example `timeout` on `web.type`. `kinenix validate` names each one and suggests the closest valid name.

**YAML**

- **`${...}` inside a list:** `attachments: [${config.output_path}]` is a YAML syntax error, because `{` starts a mapping inside `[ ]` (7B, 2 of 5 runs).
- **Unquoted `:` in a value:** `selector: button: Accept recommended cookies`.
- **Indentation of nested lists**, and error-handling keys placed under `with:`.
- When written by hand, `selector: #dropdownCurrency` silently became an empty value, because `#` starts a comment. Selectors have to be quoted.

Every model also invented things the requirement did not say (URLs, config values inside `variables`, subflows that do not exist). That is a model-size problem, not a format problem, and it shrank with the larger model.

## Conclusions

1. **From 3B up, `flow.md` is the better format for AI authoring**, for both model families and on both machines. YAML's advantage on the smallest model came from `flow.md` failing silently, which is now fixed.
2. **Kinenix's `${...}` syntax and YAML conflict.** Moving to YAML would also mean changing the expression syntax.
3. **Clear errors matter more than the format.** The 7B model's `flow.md` problems were all of a kind that `kinenix validate` reports with a fix, so an assistant can correct them in one more round.
4. **Code-trained models matter more than size.** At the same 3B size, the coder model used 9.0 of the 11 actions and attached loop sub-steps in 9 of 10 runs; the general model used 6.2 and did so in 2 of 10. `qwen2.5-coder:3b` came close to `qwen2.5-coder:7b` (9.2).
5. **Model size:** 1.5B is too small to write flows in either format; a code-trained 3-4B model is usable as a first draft that `kinenix validate` then corrects; 7B is better when the machine allows it.
6. **License:** the best small model in this test, `qwen2.5-coder:3b`, is licensed for research only. `phi4-mini` (MIT) had the most clean flows (4 of 10) and is the first candidate for a default model on small machines.

## Changes made in Kinenix

- `flow.md` is the only flow file; `flow.json` is no longer written or read (`kinenix compile` prints the compiled form for inspection, `kinenix export-md` converts old JSON flows).
- A step heading without an action, and a flow without steps, are reported by `kinenix validate` and `kinenix run`.
- The sub-step indentation message shows the correct form.
- The `AGENTS.md` of every new project lists the three most common mistakes from this test.

## Limitations

- One task, two model families, and small samples (5 to 10 runs per format). The results show a direction, not exact rates.
- The two machines ran different Ollama versions (0.40.3 and 0.34.2); generation speed is not comparable across machines.
- Scores check the file, not a successful run against the site.
- The prompt was written by the Kinenix authors, who know `flow.md` well; a different prompt could change the numbers.

## Reproduce

```bash
cd benchmarks/flow_format
pip install requests pyyaml                # only for this benchmark
ollama pull qwen2.5-coder:7b
kinenix actions > actions.txt
python experiment.py qwen2.5-coder:7b 5 --machine my-pc   # writes results/my-pc/<model>/runN.md, runN.yaml, scores.jsonl
python experiment.py --rescore                             # score every saved flow again and print the table
```

## Next benchmarks

Planned, to cover what this one did not:

| Benchmark | Question |
| :--- | :--- |
| More tasks | Do the results hold for `hello`, `rpachallenge`, and a long real requirement (insurance quotes with subflows)? |
| Run success | Does the generated flow actually run, against the example sites and the test sites listed in [roadmap.md](../roadmap.md)? |
| Repair rounds | Given the `kinenix validate` output, how many rounds does each model need to reach a clean flow? |
| More models | `qwen3:4b`, Gemma, Granite (IBM), Llama, Typhoon for Thai requirements, and larger models on a GPU machine; Apache 2.0 and MIT models first |
| Thai requirements | The same tasks with the requirement written in Thai |
| Error explanation | For the Phase 2 run records: does a local model explain a recorded failure correctly the next morning? |

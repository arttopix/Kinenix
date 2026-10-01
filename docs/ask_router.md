# Ask Router (Natural-Language Questions) - Work in Progress

Goal: let a user ask the Orchestrator questions such as "เมื่อคืนมี job ไหนพังบ้าง" at any time and get an answer built from real execution data, using a local model only.

Status as of 2026-10-01: question understanding and the decision policy are built and measured on the tune split. Nothing answers questions end to end yet. The code was merged into `dev` in PR #19.

---

## 1. Design

```text
question
  -> route()   OpenThai-SystemOne picks tool, status, window, flow as choice questions (one request)
  -> decide()  per field: answer, ask back, or use a safe default
  -> resolve   window name -> concrete timestamps (Asia/Bangkok)           [not built]
  -> tool      read-only query against the Orchestrator database          [not built]
  -> reply     Thai template filled from query results                    [not built]
```

- The model never writes SQL or free text. It only chooses among options defined in code, and every number in a reply comes from a query.
- Time windows are resolved by code, not by the model.
- Data stays on the machine (OpenThai-SystemOne runs locally).

## 2. What Exists

| Item | Location |
| :--- | :--- |
| Options, descriptions, `route()`, `decide()` | `kinenix-orchestrator/kinenix_orchestrator/services/ask_router.py` |
| Unit tests for `decide()` (no model needed) | `kinenix-orchestrator/tests/test_ask_router.py` |
| 50 labelled questions (30 tune, 20 holdout) | `kinenix-orchestrator/tests/eval/ask_router_cases.yaml` |
| Evaluation script | `kinenix-orchestrator/tests/eval/run_ask_router_eval.py` |
| Reports and saved model answers (gitignored) | `kinenix-orchestrator/tests/eval/results/` |

Options:

- **tool:** `search_executions`, `get_execution_detail`, `get_flow_history`, `get_worker_status`, `find_missed_runs`, `unrelated`
- **status:** `failed`, `success`. `all` was removed because it absorbed most failure questions.
- **window:** `last_hour`, `last_night`, `today`, `yesterday`, `last_7_days`, `custom`
- **flow:** names from the database, plus `none`

`decide()` policy (threshold 0.5):

| Field | When unsure |
| :--- | :--- |
| tool | Ask what the user wants |
| status | Do not filter; list every run with failures first |
| window | Ask which window; `get_flow_history` uses the last 7 days |
| flow | Ask which flow; `get_execution_detail` with no flow named explains the latest failure |

## 3. Results So Far (tune split, 30 cases)

| Change | tool | all fields | Answered correctly / asked / wrong at t=0.5 |
| :--- | :--- | :--- | :--- |
| First run | 71% | 43% | (old min-confidence policy) |
| Remove status `all` | 71% | 61% | |
| Distinct tool descriptions (variant B) | 86% | 71% | |
| Variant B plus short English hints | 82% | 79% | 17 / 13 / 1 (old policy, t=0.5) |
| Per-field `decide()` policy | 82% | 79% | 22 / 6 / 2 |
| `find_missed_runs` description V1 (current) | 93% | - | 24 / 5 / 1 |

Findings:

- Option descriptions matter far more than option names; Thai option names did not help.
- Descriptions must state what separates a tool from its neighbours, not list keywords.
- The four questions in one request affect each other; always rerun the full evaluation.
- A low window confidence often means the tool itself is wrong, so an unsure window asks back instead of defaulting.
- SystemOne `confidence` is not the top probability; it also reflects `abstain` and the margin between options.
- The model is deterministic for the same input, so differences between runs come from changes, not noise.
- Latency is 4-9 s per question because `torch` in `.venv` is the CPU build; the machine has an RTX 3050 Ti (4 GB).

`find_missed_runs` now reads "ถามว่างานตามตารางได้รันจริงหรือเปล่า หรือมีงานที่ควรรันแต่ไม่ได้รัน ..." (V1 of three tried; answers in `tests/eval/results/tune_answers_missed_V*.json`). It fixed t25. The only remaining wrong case at t=0.5 is t26 "งานรอบตี 3 เมื่อคืนรันหรือเปล่า": the tool is now correct, but the window is `last_night` instead of `custom`. A last-night search would still contain a 03:00 run, so the label may be too strict.

## 4. Remaining Work

In order:

1. Decide whether t26 should accept `last_night`, then run the holdout split once and pick the threshold (0.5 or 0.6). The saved answers in `results/` predate V1; rerun the tune split with `--json` before replaying policies.
2. Window resolver: map window names to timestamps in `Asia/Bangkok` (add a `BUSINESS_TIMEZONE` setting).
3. Read-only tools on the existing `executions` table: `search_executions`, `get_execution_detail`, `get_flow_history`. Redact flow `variables` from `raw_log` before any model sees them.
4. Thai reply templates that always state the window searched.
5. `POST /api/v1/ask` behind dashboard auth, and a chat box on the dashboard.
6. Parser for explicit clock ranges (`custom`, for example "ตี 2 ถึงตี 4").
7. Blocked by other work:
   - `get_worker_status` needs workers to send heartbeats.
   - `find_missed_runs` needs a `schedules` table.
8. Optional: CUDA `torch` for speed; `pyyaml` in the Orchestrator `[dev]` extra for the evaluation script; short flow IDs (for example `A01`) so users do not have to type long flow names.

## 5. How to Resume

```powershell
# Start SystemOne (model is cached locally)
$env:OPENTHAI_SYSTEMONE_MODEL = "iapp/OpenThai-SystemOne"
.venv\Scripts\python.exe -m uvicorn openthai_systemone.server:app --host 127.0.0.1 --port 8000

# Evaluate the tune split and write a readable report
.venv\Scripts\python.exe kinenix-orchestrator/tests/eval/run_ask_router_eval.py --split tune --json kinenix-orchestrator/tests/eval/results/tune_answers.json --report kinenix-orchestrator/tests/eval/results/tune.md

# Try decide() policy changes without calling the model
.venv\Scripts\python.exe kinenix-orchestrator/tests/eval/run_ask_router_eval.py --split tune --from-json kinenix-orchestrator/tests/eval/results/tune_answers.json
```

Do not look at holdout results while tuning; run the holdout split once at the end.

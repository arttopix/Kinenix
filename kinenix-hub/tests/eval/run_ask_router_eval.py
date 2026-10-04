"""Measure how well OpenThai-SystemOne routes questions in ask_router_cases.yaml.

Requires a running SystemOne server:
    OPENTHAI_SYSTEMONE_MODEL=iapp/OpenThai-SystemOne uvicorn openthai_systemone.server:app --port 8000

Usage (from the repository root):
    python kinenix-hub/tests/eval/run_ask_router_eval.py --split tune
    python kinenix-hub/tests/eval/run_ask_router_eval.py --split holdout --json results.json
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

import yaml

from kinenix_hub.services.ask_router import decide, route

CASES_FILE = Path(__file__).with_name("ask_router_cases.yaml")
SCORED_FIELDS = ["tool", "status", "window", "flow"]
THRESHOLDS = [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
POLICY = {"default_window": False}


def run_case(case, flow_names, url):
    out = route(case["q"], flow_names, url=url)
    predicted = {f: out["answers"][f]["choice"] for f in SCORED_FIELDS}
    expect = case["expect"]
    field_ok = {f: predicted[f] == expect[f] for f in SCORED_FIELDS if f in expect}
    return {
        "id": case["id"],
        "q": case["q"],
        "expect": expect,
        "predicted": predicted,
        "field_ok": field_ok,
        "all_ok": all(field_ok.values()) if field_ok else None,
        "ask_back_expected": bool(expect.get("ask_back")),
        "confidence": out["confidence"],
        "field_confidence": {f: out["answers"][f]["confidence"] for f in SCORED_FIELDS},
        "probabilities": {f: out["answers"][f].get("probabilities", {}) for f in SCORED_FIELDS},
        "tool_abstain": out["answers"]["tool"].get("abstain"),
        "latency_ms": out["latency_ms"],
        "answers": out["answers"],
        "note": case.get("note"),
    }


def outcome(r, threshold):
    """Grade the decide() result: ok, ok_default, asked, or wrong.

    ok_default means correct but a field fell back to a default (status unfiltered,
    or the default window happened to match). Asking back is never counted as wrong.
    """
    d = decide(r["answers"], threshold, **POLICY)
    expect = r["expect"]
    if r["ask_back_expected"]:
        return ("ok" if d["action"] in ("clarify", "unrelated") else "wrong"), d
    if expect.get("tool") == "unrelated":
        return {"unrelated": "ok", "clarify": "asked"}.get(d["action"], "wrong"), d
    if d["action"] == "clarify":
        return "asked", d
    if d["action"] == "unrelated" or d["tool"] != expect.get("tool"):
        return "wrong", d
    for field in ("status", "window", "flow"):
        if field not in expect or field not in d["params"]:
            continue
        value = d["params"][field]
        if field == "status" and value is None:
            continue  # unfiltered list still contains the runs asked about
        if value != expect[field]:
            return "wrong", d
    return ("ok_default" if d["defaulted"] else "ok"), d


def sweep(results):
    rows = []
    for t in THRESHOLDS:
        counts = {"ok": 0, "ok_default": 0, "asked": 0, "wrong": 0}
        for r in results:
            counts[outcome(r, t)[0]] += 1
        rows.append((t, counts))
    return rows


def _describe(d):
    if d["action"] == "clarify":
        return f"clarify {d['clarify']}"
    if d["action"] == "unrelated":
        return "unrelated"
    params = ", ".join(f"{k}={v}" for k, v in d["params"].items())
    defaulted = f" (default: {', '.join(d['defaulted'])})" if d["defaulted"] else ""
    return f"{d['tool']}({params}){defaulted}"


def _top(probabilities, n=3):
    ranked = sorted(probabilities.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return ", ".join(f"{name} {p:.2f}" for name, p in ranked)


def write_report(path, split, results, summary_lines):
    """Readable Markdown report: summary, then every question with the model's answer per field."""
    lines = [f"# Ask router evaluation ({split})", "", "```text", *summary_lines, "```", ""]
    for r in results:
        if r["ask_back_expected"]:
            verdict = "EXPECT ASK BACK"
        else:
            verdict = "OK" if r["all_ok"] else "WRONG"
        lines += [
            f"## {r['id']}  {verdict}  (confidence {r['confidence']:.2f})",
            "",
            f"> {r['q']}",
            "",
            "| field | expected | predicted | confidence | top 3 options |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for f in SCORED_FIELDS:
            expected = r["expect"].get(f, "-")
            mark = ""
            if f in r["field_ok"]:
                mark = " (ok)" if r["field_ok"][f] else " **(wrong)**"
            lines.append(
                f"| {f} | {expected} | {r['predicted'][f]}{mark} | {r['field_confidence'][f]:.2f} | {_top(r['probabilities'][f])} |"
            )
        if r.get("decision"):
            lines.append(f"\ndecision: **{r['verdict']}**  {_describe(r['decision'])}")
        if r.get("tool_abstain") is not None:
            lines.append(f"\ntool abstain (none of the options): {r['tool_abstain']:.2f}")
        if r.get("note"):
            lines.append(f"\nnote: {r['note']}")
        lines.append("")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["tune", "holdout", "all"], default="tune")
    parser.add_argument("--url", default="http://127.0.0.1:8000/v1/systemone")
    parser.add_argument("--json", help="Write per-case results to this file")
    parser.add_argument("--report", help="Write a readable Markdown report to this file")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold for the per-case decisions")
    parser.add_argument("--default-window", action="store_true", help="Use a default window instead of asking when the window is unsure")
    parser.add_argument("--from-json", help="Reuse model answers saved with --json instead of calling SystemOne")
    args = parser.parse_args()

    cases = yaml.safe_load(CASES_FILE.read_text(encoding="utf-8"))
    if args.split != "all":
        cases = [c for c in cases if c["split"] == args.split]
    flow_names = sorted({c["expect"]["flow"] for c in yaml.safe_load(CASES_FILE.read_text(encoding="utf-8")) if "flow" in c["expect"]})

    POLICY["default_window"] = args.default_window
    if args.from_json:
        saved = {r["id"]: r for r in json.loads(Path(args.from_json).read_text(encoding="utf-8"))}
        results = [saved[c["id"]] for c in cases]
    else:
        results = [run_case(c, flow_names, args.url) for c in cases]
    scored = [r for r in results if not r["ask_back_expected"]]
    n_ask = len(results) - len(scored)

    out = []
    out.append(f"split={args.split}  cases={len(results)}  (ask_back cases: {n_ask})  policy={POLICY}")
    out.append(f"latency: median {statistics.median(r['latency_ms'] for r in results):.0f} ms, "
               f"max {max(r['latency_ms'] for r in results):.0f} ms")
    out.append("")
    out.append("Raw accuracy (ignores confidence)")
    for f in SCORED_FIELDS:
        rs = [r for r in scored if f in r["field_ok"]]
        if rs:
            ok = sum(r["field_ok"][f] for r in rs)
            out.append(f"  {f:<8} {ok:>2}/{len(rs):<2}  {ok / len(rs):.0%}")
    ok_all = sum(1 for r in scored if r["all_ok"])
    out.append(f"  {'all':<8} {ok_all:>2}/{len(scored):<2}  {ok_all / len(scored):.0%}")
    out.append("")
    out.append("Decision sweep (per-field decide())")
    out.append(f"  {'t':>4}  {'ok':>4}  {'ok_default':>10}  {'asked':>5}  {'wrong':>5}")
    for t, c in sweep(results):
        out.append(f"  {t:>4.1f}  {c['ok']:>4}  {c['ok_default']:>10}  {c['asked']:>5}  {c['wrong']:>5}")
    out.append("")
    out.append(f"Decisions at t={args.threshold}")
    for r in results:
        verdict, d = outcome(r, args.threshold)
        r["decision"], r["verdict"] = d, verdict
        if verdict != "ok":
            out.append(f"  {r['id']}  {verdict:<10}  {_describe(d)}  | {r['q']}")
    out.append("")
    out.append("Mistakes")
    for r in results:
        if r["ask_back_expected"]:
            out.append(f"  {r['id']}  [ask_back] conf={r['confidence']:.2f}  predicted tool={r['predicted']['tool']}  {r['q']}")
            continue
        bad = [f for f, ok in r["field_ok"].items() if not ok]
        if bad:
            detail = ", ".join(f"{f}: {r['predicted'][f]} ({r['field_confidence'][f]:.2f}) expected {r['expect'][f]}" for f in bad)
            out.append(f"  {r['id']}  conf={r['confidence']:.2f}  {detail}  | {r['q']}")
    print("\n".join(out))

    if args.report:
        write_report(args.report, args.split, results, out)
    if args.json:
        Path(args.json).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

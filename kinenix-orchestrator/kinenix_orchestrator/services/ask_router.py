"""Route a free-form question about jobs and workers to a read-only tool.

OpenThai-SystemOne picks the tool and its categorical parameters (status, time
window, flow) as choice questions in a single request. It never generates text,
so every parameter is constrained to the options defined here. Time windows are
resolved to concrete timestamps by code, not by the model.
"""
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

from ..config import CENTRAL_LLM_URL

# Each description states what separates the tool from its neighbours. Keyword lists
# overlapped (for example "พัง" in both search and history) and confused the model.
TOOL_OPTIONS: Dict[str, str] = {
    "search_executions": "ถามว่าในช่วงเวลาหนึ่งมีงานอะไรรันบ้าง พังหรือผ่าน โดยไม่ได้เจาะจง flow เดียว เช่น เมื่อคืนพังไหม มี error ไหม (list runs, failed jobs)",
    "get_execution_detail": "ถามหาสาเหตุหรือวิธีแก้ของงานที่พังแล้ว เช่น พังเพราะอะไร แก้ยังไง",
    "get_flow_history": "เจาะจงชื่อ flow หนึ่งตัว แล้วถามแนวโน้มหลายวัน เช่น flow นี้พังบ่อยไหม เสถียรไหม เริ่มพังเมื่อไร",
    "get_worker_status": "ถามสถานะเครื่อง worker หรือ Raspberry Pi ตอนนี้ ไม่ใช่เรื่องงาน",
    "find_missed_runs": "ถามว่างานตามตารางได้รันจริงหรือเปล่า หรือมีงานที่ควรรันแต่ไม่ได้รัน ตกหล่น รันครบไหม (ไม่ใช่งานที่รันแล้วพัง) (missed runs that never started)",
    "unrelated": "เรื่องอื่นที่ไม่เกี่ยวกับงาน flow หรือเครื่อง worker",
}

STATUS_OPTIONS: Dict[str, str] = {
    "failed": "งานที่พัง ล้มเหลว error ไม่ผ่าน ล่ม fail",
    "success": "งานที่สำเร็จ ผ่าน รันได้ success",
}

WINDOW_OPTIONS: Dict[str, str] = {
    "last_hour": "ชั่วโมงที่ผ่านมา เมื่อกี้ เมื่อสักครู่ 1 ชม.ล่าสุด",
    "last_night": "เมื่อคืน คืนที่ผ่านมา ช่วงกลางคืน last night",
    "today": "วันนี้ ตั้งแต่เช้า today",
    "yesterday": "เมื่อวานทั้งวัน yesterday",
    "last_7_days": "สัปดาห์นี้ อาทิตย์นี้ 7 วันที่ผ่านมา",
    "custom": "ระบุเวลาเป็นชั่วโมงหรือนาฬิกา เช่น ตี 2 ถึงตี 4 หรือ 22:00",
}

NO_FLOW = "none"

# Parameters that matter for each tool; used to compute an overall confidence
TOOL_FIELDS: Dict[str, List[str]] = {
    "search_executions": ["status", "window"],
    "get_execution_detail": ["flow"],
    "get_flow_history": ["flow"],
    "get_worker_status": [],
    "find_missed_runs": ["window"],
    "unrelated": [],
}


def build_questions(flow_names: Iterable[str]) -> Dict[str, Any]:
    flow_criteria: Dict[str, Optional[str]] = {NO_FLOW: "ไม่ได้ระบุชื่อ flow หรือหมายถึงทุก flow"}
    for name in flow_names:
        flow_criteria[name] = None
    return {
        "tool": {"type": "choice", "instructions": "ผู้ใช้ต้องการข้อมูลแบบไหน", "criteria": TOOL_OPTIONS},
        "status": {"type": "choice", "instructions": "ผู้ใช้สนใจงานสถานะไหน", "criteria": STATUS_OPTIONS},
        "window": {"type": "choice", "instructions": "ผู้ใช้ถามถึงช่วงเวลาไหน", "criteria": WINDOW_OPTIONS},
        "flow": {"type": "choice", "instructions": "ผู้ใช้พูดถึง flow ชื่ออะไร", "criteria": flow_criteria},
    }


def route(question: str, flow_names: Iterable[str], url: str = CENTRAL_LLM_URL, timeout: float = 30.0) -> Dict[str, Any]:
    """Return {"answers": {field: {choice, confidence, probabilities, abstain}}, "confidence", "latency_ms"}.

    `confidence` is the lowest confidence among the tool and the fields that tool uses.
    """
    payload = {"state": f"คำถามของผู้ใช้: {question}", "questions": build_questions(flow_names)}
    started = time.perf_counter()
    res = requests.post(url, json=payload, timeout=timeout)
    res.raise_for_status()
    latency_ms = (time.perf_counter() - started) * 1000
    answers = res.json()["answers"]

    tool = answers["tool"]["choice"]
    relevant = [answers["tool"]["confidence"]] + [answers[f]["confidence"] for f in TOOL_FIELDS.get(tool, [])]
    return {"answers": answers, "confidence": min(relevant), "latency_ms": latency_ms}


# Window used when the model is unsure; the reply states the window so the user can correct it
DEFAULT_WINDOW: Dict[str, str] = {
    "search_executions": "last_night",
    "find_missed_runs": "last_night",
    "get_flow_history": "last_7_days",
}


def decide(answers: Dict[str, Any], threshold: float = 0.5, default_window: bool = False) -> Dict[str, Any]:
    """Turn SystemOne answers into an action, deciding each field separately.

    Returns {"action": "answer" | "clarify" | "unrelated", "tool", "params", "defaulted", "clarify"}:
    - an unsure tool asks the user what they want (clarify="tool")
    - an unsure status means no status filter (show every run, failures first)
    - an unsure window asks which window (clarify="window"), except get_flow_history, which
      uses DEFAULT_WINDOW; default_window=True uses DEFAULT_WINDOW for every tool instead
    - get_flow_history needs one flow; an unsure or missing flow asks which flow (clarify="flow")
    - get_execution_detail with no flow named explains the latest failed run; an unsure flow name asks
    """
    def sure(field: str) -> bool:
        return answers[field]["confidence"] >= threshold

    tool = answers["tool"]["choice"]
    result: Dict[str, Any] = {"action": "answer", "tool": tool, "params": {}, "defaulted": [], "clarify": None}

    if not sure("tool"):
        result.update(action="clarify", clarify="tool")
        return result
    if tool == "unrelated":
        result["action"] = "unrelated"
        return result

    params = result["params"]
    if tool == "search_executions":
        if sure("status"):
            params["status"] = answers["status"]["choice"]
        else:
            params["status"] = None
            result["defaulted"].append("status")

    if tool in DEFAULT_WINDOW:
        if sure("window"):
            params["window"] = answers["window"]["choice"]
        elif default_window or tool == "get_flow_history":
            # History questions rarely name a window ("since when"); a week is a safe default
            params["window"] = DEFAULT_WINDOW[tool]
            result["defaulted"].append("window")
        else:
            result.update(action="clarify", clarify="window")
            return result

    if tool in ("get_flow_history", "get_execution_detail"):
        flow = answers["flow"]["choice"]
        if flow != NO_FLOW and sure("flow"):
            params["flow"] = flow
        elif tool == "get_execution_detail" and flow == NO_FLOW:
            params["flow"] = None  # no flow named: explain the latest failed run
        else:
            result.update(action="clarify", clarify="flow")
    return result

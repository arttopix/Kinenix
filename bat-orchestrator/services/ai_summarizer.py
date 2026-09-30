import logging
from typing import Any, Dict, Optional, Tuple
import requests

from ..config import CENTRAL_LLM_URL

logger = logging.getLogger("batautomate.orchestrator.ai")

CATEGORIES = {
    "Cookie Consent / Security Modal": {
        "th_label": "หน้าต่าง Cookie หรือการยืนยันสิทธิ์",
        "root_cause": "หน้าต่าง Cookie หรือป๊อปอัปความยินยอมไม่ปรากฏ หรือเคยถูกยอมรับไปแล้ว ทำให้ปุ่มเป้าหมายหายไปจากหน้าจอ",
        "suggestion": "ใช้ Action web.is_visible เพื่อตรวจสอบก่อนกด หรือใส่ optional: true ใน web.click"
    },
    "UI Selector Not Found / DOM Changed": {
        "th_label": "หาปุ่มหรือ Element ไม่พบบนหน้าเว็บ (โครงสร้างเปลี่ยน)",
        "root_cause": "Selector หรือ XPath ไม่ตรงกับโครงสร้าง HTML ปัจจุบันของเว็บไซต์",
        "suggestion": "ตรวจสอบ Selector ใน DevTools หรือใช้ ai_match: true ช่วยจับคู่แบบ Semantic"
    },
    "Page Load / Network Timeout": {
        "th_label": "เครือข่ายขัดข้อง หรือหน้าเว็บโหลดช้าเกินกำหนด",
        "root_cause": "เว็บไซต์ตอบสนองช้าเกินกว่าเวลา Timeout หรืออินเทอร์เน็ตขัดข้องระหว่างโหลดข้อมูล",
        "suggestion": "เพิ่ม timeout ใน web.wait_for หรือตั้งค่า on_error: retry พร้อม max_retries: 2"
    },
    "File / Resource Missing": {
        "th_label": "ไม่พบไฟล์ที่จำเป็น (เช่น Excel หรือโฟลเดอร์)",
        "root_cause": "ไฟล์เป้าหมายไม่มีอยู่ในระบบ หรือระบุพาธผิดพลาด",
        "suggestion": "ตรวจสอบว่าสร้างไฟล์สำเร็จในขั้นตอนก่อนหน้า และพาธเป็น Relative Path ที่ถูกต้อง"
    },
    "Data Validation / Format Error": {
        "th_label": "ข้อมูลไม่ตรงรูปแบบ หรือตารางไม่มีข้อมูล",
        "root_cause": "ค่าที่ดึงมาได้จากหน้าเว็บว่างเปล่า หรือรูปแบบวันที่/ตัวเลขไม่ถูกต้อง",
        "suggestion": "ตรวจสอบข้อมูลของช่วงวันที่ที่เลือก หรือเพิ่มขั้นตอน logic.if ตรวจสอบค่าว่าง"
    }
}


def analyze_failure(
    flow_name: str,
    failed_step_name: Optional[str],
    error_message: Optional[str],
    exception_class: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes an automation failure using Central OpenThai-SystemOne model
    to classify the error category and generate an executive Thai summary.
    """
    err_text = error_message or ""
    step_desc = failed_step_name or "ไม่ระบุขั้นตอน"

    # Default fallback classification
    best_category = "UI Selector Not Found / DOM Changed"
    confidence = 0.85

    # 1. Try invoking OpenThai-SystemOne on Port 8000
    try:
        criteria = {cat: None for cat in CATEGORIES.keys()}
        payload = {
            "type": "choice",
            "instructions": f"วิเคราะห์ประเภทของความผิดพลาดในระบบบอทอัตโนมัติจากข้อความ Error: '{err_text}' ที่ขั้นตอน: '{step_desc}'",
            "criteria": criteria
        }
        res = requests.post(CENTRAL_LLM_URL, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and "choice" in data:
                detected_choice = data["choice"]
                if detected_choice in CATEGORIES:
                    best_category = detected_choice
                    confidence = float(data.get("score", 0.92))
    except Exception as e:
        logger.warning(f"Central OpenThai server call failed, using rule-based triage: {e}")
        # Rule-based fallback
        lower_err = err_text.lower()
        if "cookie" in lower_err or "consent" in lower_err:
            best_category = "Cookie Consent / Security Modal"
        elif "timeout" in lower_err or "timeoutexceeded" in lower_err or "wait_for" in lower_err:
            best_category = "Page Load / Network Timeout"
        elif "not found" in lower_err or "filenotfound" in lower_err:
            best_category = "File / Resource Missing"

    cat_meta = CATEGORIES.get(best_category, list(CATEGORIES.values())[0])

    # 2. Synthesize clear Thai Executive Summary
    summary_text = (
        f"บอทไม่สามารถทำงานต่อได้ที่ขั้นตอน '{step_desc}' ของ Flow '{flow_name}' "
        f"เนื่องจาก {cat_meta['root_cause']}"
    )

    return {
        "category": cat_meta["th_label"],
        "confidence": round(confidence * 100, 1),
        "summary": summary_text,
        "root_cause": cat_meta["root_cause"],
        "suggestion": cat_meta["suggestion"]
    }


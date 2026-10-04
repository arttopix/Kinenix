from kinenix_hub.services.ask_router import NO_FLOW, decide


def _answers(tool, tool_conf=0.9, status=("failed", 0.9), window=("last_night", 0.9), flow=(NO_FLOW, 0.9)):
    return {
        "tool": {"choice": tool, "confidence": tool_conf},
        "status": {"choice": status[0], "confidence": status[1]},
        "window": {"choice": window[0], "confidence": window[1]},
        "flow": {"choice": flow[0], "confidence": flow[1]},
    }


def test_confident_search_uses_all_fields():
    d = decide(_answers("search_executions"))
    assert d["action"] == "answer"
    assert d["params"] == {"status": "failed", "window": "last_night"}
    assert d["defaulted"] == []


def test_unsure_tool_asks_back():
    d = decide(_answers("search_executions", tool_conf=0.2))
    assert d["action"] == "clarify"
    assert d["clarify"] == "tool"


def test_unsure_status_removes_the_filter():
    d = decide(_answers("search_executions", status=("failed", 0.1)))
    assert d["action"] == "answer"
    assert d["params"]["status"] is None
    assert d["defaulted"] == ["status"]


def test_unsure_window_asks_back_for_search():
    d = decide(_answers("search_executions", window=("today", 0.2)))
    assert d["action"] == "clarify"
    assert d["clarify"] == "window"


def test_unsure_window_uses_default_when_enabled():
    d = decide(_answers("find_missed_runs", window=("today", 0.2)), default_window=True)
    assert d["action"] == "answer"
    assert d["params"]["window"] == "last_night"
    assert d["defaulted"] == ["window"]


def test_flow_history_defaults_window_and_requires_flow():
    d = decide(_answers("get_flow_history", window=("today", 0.2), flow=("RPA Challenge Solver", 0.9)))
    assert d["action"] == "answer"
    assert d["params"] == {"window": "last_7_days", "flow": "RPA Challenge Solver"}

    d = decide(_answers("get_flow_history", flow=(NO_FLOW, 0.9)))
    assert d["action"] == "clarify"
    assert d["clarify"] == "flow"


def test_execution_detail_without_flow_explains_latest_failure():
    d = decide(_answers("get_execution_detail", flow=(NO_FLOW, 0.3)))
    assert d["action"] == "answer"
    assert d["params"] == {"flow": None}


def test_execution_detail_with_unsure_flow_asks_back():
    d = decide(_answers("get_execution_detail", flow=("RPA Challenge Solver", 0.3)))
    assert d["action"] == "clarify"
    assert d["clarify"] == "flow"


def test_unrelated_and_worker_status_need_no_parameters():
    assert decide(_answers("unrelated"))["action"] == "unrelated"
    d = decide(_answers("get_worker_status", status=("failed", 0.0), window=("today", 0.0)))
    assert d["action"] == "answer"
    assert d["params"] == {}

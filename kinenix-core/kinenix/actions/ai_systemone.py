import json
import logging
from typing import Any, Dict, List, Optional, Union
import requests

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext

logger = logging.getLogger("kinenix.ai_systemone")


def call_systemone_api(
    state: Union[str, Dict[str, Any]],
    questions: Dict[str, Any],
    base_url: str = "http://localhost:8000",
    timeout: float = 30.0,
    fallback_to_ollama: bool = False
) -> Dict[str, Any]:
    """
    Sends a structured decision request to a local or remote OpenThai-SystemOne API server.
    Converts friendly parameter formats (e.g. options list) to the model's required format.
    """
    clean_url = str(base_url).rstrip("/")
    endpoint = f"{clean_url}/v1/systemone"

    # Normalize state to string if dict or primitive
    normalized_state: str = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)

    # Normalize questions payload
    normalized_questions: Dict[str, Any] = {}
    for q_key, q_val in questions.items():
        if not isinstance(q_val, dict):
            continue

        q_type = str(q_val.get("type", "choice")).lower()
        instructions = q_val.get("instructions") or q_val.get("instruction") or f"Select the best match for {q_key}"
        criteria = q_val.get("criteria")

        if criteria is None:
            # Convert list of options to criteria dict (option -> None)
            options_list = q_val.get("options") or []
            if isinstance(options_list, list):
                criteria = {str(opt): None for opt in options_list}
            elif isinstance(options_list, dict):
                criteria = options_list
            else:
                criteria = {}

        if q_type == "choice":
            normalized_questions[q_key] = {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria
            }
        elif q_type == "score":
            normalized_questions[q_key] = {
                "type": "score",
                "instructions": instructions,
                "criteria": criteria or {"1": "low", "2": "medium", "3": "high"}
            }
        elif q_type in ("noul", "yes_no", "boolean"):
            normalized_questions[q_key] = {
                "type": "noul",
                "instructions": instructions
            }
        else:
            normalized_questions[q_key] = q_val

    payload = {
        "state": normalized_state,
        "questions": normalized_questions
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as conn_err:
        if fallback_to_ollama:
            logger.warning(
                f"OpenThai-SystemOne server at '{endpoint}' unreachable. Attempting fallback to local Ollama..."
            )
            return _fallback_ollama_decision(normalized_state, normalized_questions, timeout=timeout)
        raise ConnectionError(
            f"Failed to connect to OpenThai-SystemOne server at '{endpoint}'. "
            "Ensure the server is running (e.g. '$env:OPENTHAI_SYSTEMONE_MODEL=\"iapp/OpenThai-SystemOne\"; uvicorn openthai_systemone.server:app --port 8000')."
        ) from conn_err
    except Exception as e:
        raise RuntimeError(f"OpenThai-SystemOne request error: {e}") from e


def _fallback_ollama_decision(state: str, questions: Dict[str, Any], timeout: float = 60.0) -> Dict[str, Any]:
    """
    Fallback resolver using Ollama if OpenThai-SystemOne server is offline.
    """
    ollama_url = "http://localhost:11434/api/generate"
    answers = {}

    for q_key, q_val in questions.items():
        q_type = q_val.get("type", "choice")
        instructions = q_val.get("instructions", "")
        criteria = q_val.get("criteria", {})
        options = list(criteria.keys())

        prompt = (
            f"Context: {state}\n"
            f"Question: {instructions}\n"
            f"Options: {json.dumps(options, ensure_ascii=False)}\n"
            f"Return JSON: {{\"choice\": \"<selected option>\"}}"
        )

        try:
            res = requests.post(
                ollama_url,
                json={"model": "qwen2.5:1.5b", "prompt": prompt, "format": "json", "stream": False},
                timeout=timeout
            )
            res.raise_for_status()
            res_data = res.json()
            parsed = json.loads(res_data.get("response", "{}"))
            answers[q_key] = {
                "type": q_type,
                "choice": parsed.get("choice") or (options[0] if options else None),
                "confidence": 0.5,
                "fallback": "ollama"
            }
        except Exception as ex:
            logger.warning(f"Ollama fallback failed for question '{q_key}': {ex}")
            answers[q_key] = {
                "type": q_type,
                "choice": options[0] if options else None,
                "confidence": 0.0,
                "error": str(ex)
            }

    return {"model": "ollama-fallback", "answers": answers, "usage": {"input_tokens": 0, "output_tokens": 0}}


@register_action("ai.decide")
class AiDecideAction(BaseAction):
    """
    Executes fast semantic decisions (Choice, Score, Yes/No) using OpenThai-SystemOne (0.8B).
    Computes calibrated probabilities in a single forward pass without text generation hallucination.
    """
    accepted_parameters = ('base_url', 'fallback_to_ollama', 'question', 'questions', 'state', 'timeout')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        state = parameters.get("state")
        if state is None:
            raise ValueError("Parameter 'state' is required for action 'ai.decide'.")

        base_url = str(parameters.get("base_url", "http://localhost:8000"))
        timeout = float(parameters.get("timeout", 30.0))
        fallback_to_ollama = bool(parameters.get("fallback_to_ollama", True))

        # Accept either 'question' (singular) or 'questions' (plural dictionary)
        single_question = parameters.get("question")
        questions_dict = parameters.get("questions")

        if single_question and isinstance(single_question, dict):
            q_name = single_question.get("name", "decision")
            questions = {q_name: single_question}
            is_single = True
        elif questions_dict and isinstance(questions_dict, dict):
            questions = questions_dict
            is_single = False
        else:
            raise ValueError("Either 'question' (dict) or 'questions' (dict) parameter is required for 'ai.decide'.")

        response = call_systemone_api(
            state=state,
            questions=questions,
            base_url=base_url,
            timeout=timeout,
            fallback_to_ollama=fallback_to_ollama
        )

        answers = response.get("answers", {})

        if is_single and len(answers) == 1:
            # For convenient single-question calls, unwrap the direct answer
            single_res = list(answers.values())[0]
            return {
                "choice": single_res.get("choice"),
                "confidence": single_res.get("confidence"),
                "probabilities": single_res.get("probabilities", {}),
                "type": single_res.get("type"),
                "model": response.get("model", "openthai-systemone")
            }

        return {
            "answers": answers,
            "model": response.get("model", "openthai-systemone"),
            "usage": response.get("usage", {})
        }


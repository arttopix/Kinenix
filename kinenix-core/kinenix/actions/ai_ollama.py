import base64
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext

logger = logging.getLogger("kinenix")


def _resolve_file_path(file_path: str, context: ExecutionContext) -> Path:
    target_path = Path(file_path)
    if not target_path.is_absolute():
        flow_dir_str = context.get_variable("__flow_dir__")
        if flow_dir_str:
            target_path = Path(flow_dir_str) / file_path
    return target_path


def _clean_json_text(text: str) -> str:
    """
    Strips markdown code fences (e.g. ```json ... ```) from LLM output.
    """
    stripped = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return stripped


@register_action("ai.prompt")
class OllamaPromptAction(BaseAction):
    """
    Executes a prompt against a local Ollama service.
    Supports structured JSON enforcement and image inputs (multimodal).
    """
    accepted_parameters = ('base_url', 'format', 'image_path', 'model', 'prompt', 'system', 'temperature', 'timeout')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        prompt = str(parameters.get("prompt", "")).strip()
        system = parameters.get("system")
        model = str(parameters.get("model", "qwen2.5:1.5b"))
        output_format = parameters.get("format")
        base_url = str(parameters.get("base_url", "http://localhost:11434")).rstrip("/")
        timeout = float(parameters.get("timeout", 60))
        temperature = float(parameters.get("temperature", 0.1))

        if not prompt:
            raise ValueError("Parameter 'prompt' is required for action 'ai.prompt'.")

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        if system:
            payload["system"] = str(system)

        if output_format:
            payload["format"] = output_format

        # Handle optional image path for multimodal / vision models
        image_path_str = parameters.get("image_path")
        if image_path_str:
            target_image = _resolve_file_path(image_path_str, context)
            if not target_image.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path_str}")
            with open(target_image, "rb") as img_f:
                b64_img = base64.b64encode(img_f.read()).decode("utf-8")
            payload["images"] = [b64_img]

        endpoint = f"{base_url}/api/generate"

        try:
            response = requests.post(endpoint, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectionError as conn_err:
            raise ConnectionError(
                f"Failed to connect to Ollama service at '{endpoint}'. "
                "Ensure Ollama is running (e.g. 'ollama serve' or running in the background)."
            ) from conn_err
        except Exception as req_err:
            raise RuntimeError(f"Ollama API request error: {req_err}") from req_err

        raw_response = data.get("response", "")
        parsed_output: Any = raw_response

        if output_format == "json":
            cleaned = _clean_json_text(raw_response)
            try:
                parsed_output = json.loads(cleaned)
            except Exception as json_err:
                logger.warning(f"Could not parse Ollama response as JSON: {json_err}. Returning raw text.")
                parsed_output = raw_response

        return {
            "response": parsed_output,
            "raw_text": raw_response,
            "model": model,
            "total_duration": data.get("total_duration")
        }


@register_action("ai.extract")
class OllamaExtractAction(BaseAction):
    """
    Extracts structured data entities from text or an image using Ollama.
    """
    accepted_parameters = ('base_url', 'image_path', 'instructions', 'model', 'schema', 'text', 'timeout')

    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        schema: Optional[Any] = parameters.get("schema")
        instructions = parameters.get("instructions", "Extract all key invoice fields into JSON.")
        text = parameters.get("text", "")
        image_path_str = parameters.get("image_path")
        model = str(parameters.get("model", "qwen2.5:1.5b"))
        base_url = str(parameters.get("base_url", "http://localhost:11434")).rstrip("/")
        timeout = float(parameters.get("timeout", 90))

        prompt_parts: List[str] = [str(instructions)]

        if schema:
            prompt_parts.append(
                f"Required JSON schema or fields: {json.dumps(schema) if isinstance(schema, (dict, list)) else schema}"
            )

        prompt_parts.append("Respond strictly with a valid JSON object. Do not include explanatory conversational text.")

        if text:
            prompt_parts.append(f"Content to extract from:\n{text}")

        prompt = "\n\n".join(prompt_parts)

        action = OllamaPromptAction()
        action_params = {
            "prompt": prompt,
            "model": model,
            "format": "json",
            "base_url": base_url,
            "timeout": timeout,
            "temperature": 0.0
        }

        if image_path_str:
            action_params["image_path"] = image_path_str

        result = action.execute(action_params, context)
        return result.get("response")

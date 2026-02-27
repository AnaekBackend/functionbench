"""LM Studio model callable for FunctionBench: (input: str) -> str."""

import json
import os
from pathlib import Path

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:1234"
DEFAULT_MODEL = "lm-studio"

SYSTEM_PROMPT_BASE = """Respond with exactly one JSON object. No markdown, no explanation, no text before or after.

Format: {"name": "<tool_name>", "arguments": { ... }}

- Use the exact tool names and argument keys from the provided tool schema.
- For clarification, use: {"name": "ask_clarify", "arguments": {"reason": "..."}}
- Output only the single JSON object."""


def _load_tools_prompt() -> str:
    path = os.environ.get("FUNCTIONBENCH_TOOLS_JSON")
    if not path or not Path(path).exists():
        return ""
    try:
        raw = json.loads(Path(path).read_text())
        return "\n\nTool schema (use these names and argument keys):\n" + json.dumps(raw, indent=2)
    except Exception:
        return ""


def _system_prompt() -> str:
    return SYSTEM_PROMPT_BASE + _load_tools_prompt()


def lmstudio_callable(input_text: str) -> str:
    """
    Callable for FunctionBench: POSTs to LM Studio and returns the model response string.
    Env: FUNCTIONBENCH_LMSTUDIO_URL, FUNCTIONBENCH_LMSTUDIO_MODEL, optionally FUNCTIONBENCH_TOOLS_JSON.
    """
    base_url = os.environ.get("FUNCTIONBENCH_LMSTUDIO_URL", DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("FUNCTIONBENCH_LMSTUDIO_MODEL", DEFAULT_MODEL)
    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": input_text},
        ],
        "temperature": 0,
        "max_tokens": 512,
    }
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return "{}"
    try:
        content = data["choices"][0]["message"]["content"]
        return (content or "").strip() or "{}"
    except (KeyError, IndexError, TypeError):
        return "{}"

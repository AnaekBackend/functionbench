"""JSON extraction and parsing utilities."""

import json
import re
from typing import Literal


def safe_json_loads(text: str) -> dict | None:
    """Parse JSON string; return None on error."""
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def extract_json_from_text(text: str) -> tuple[dict | None, str | None]:
    """
    Extract the first valid JSON object from text.
    Handles markdown-wrapped JSON (```json ... ``` or ``` ... ```).
    Returns (parsed_dict, error_message). error_message is None on success.
    """
    if not text or not text.strip():
        return None, "empty input"

    # Try markdown code block first (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence_match:
        block = fence_match.group(1).strip()
        obj = safe_json_loads(block)
        if obj is not None:
            return obj, None
        return None, "invalid JSON in code block"

    # Find first { and then match braces to get a single JSON object
    start = text.find("{")
    if start == -1:
        return None, "no JSON object found"

    depth = 0
    in_string = False
    escape = False
    quote_char = None
    i = start

    while i < len(text):
        c = text[i]
        if escape:
            escape = False
            i += 1
            continue
        if c == "\\" and in_string:
            escape = True
            i += 1
            continue
        if in_string:
            if c == quote_char:
                in_string = False
            i += 1
            continue
        if c in ('"', "'"):
            in_string = True
            quote_char = c
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                obj = safe_json_loads(candidate)
                if obj is not None:
                    return obj, None
                return None, "invalid JSON structure"
        i += 1

    return None, "unclosed JSON object"


def extract_json_strict(
    text: str, mode: Literal["json_only", "fenced_json"]
) -> tuple[dict | None, str | None, str | None]:
    """
    Strict JSON extraction for protocol modes.

    Returns (obj, extract_error, protocol_error).
    - obj: parsed dict on success, else None.
    - extract_error: empty/no JSON/parse errors (for F8/F9 classification).
    - protocol_error: non-None when JSON is valid but protocol rules are violated (for F10).
    """
    text = text or ""
    stripped = text.strip()
    if not stripped:
        return None, "empty input", None

    # fenced_json mode: prefer fenced block, but enforce no extra text
    if mode == "fenced_json":
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
        if fence_match:
            before = stripped[: fence_match.start()]
            after = stripped[fence_match.end() :]
            if before.strip() or after.strip():
                block = fence_match.group(1)
                obj = safe_json_loads(block)
                if obj is None:
                    return None, "invalid JSON in code block", "protocol violation: extra text outside fenced block"
                return obj, None, "protocol violation: extra text outside fenced block"
            block = fence_match.group(1)
            obj = safe_json_loads(block)
            if obj is None:
                return None, "invalid JSON in code block", None
            return obj, None, None
        # fall through to json_only rules if no fence

    # json_only behavior (also fallback for fenced_json without fence)
    if not (stripped.startswith("{") and stripped.endswith("}")):
        # Could be no JSON at all or malformed; let caller classify as NOT_JSON vs PARSE_ERROR.
        # We don't attempt heuristic extraction here.
        try:
            json.loads(stripped)
            return None, "invalid JSON structure", "protocol violation: extra text outside JSON object"
        except Exception:
            if "{" not in stripped:
                return None, "no JSON object found", None
            return None, "JSON parse error", None

    try:
        obj_any = json.loads(stripped)
    except json.JSONDecodeError:
        return None, "JSON parse error", None

    if not isinstance(obj_any, dict):
        return None, "JSON top-level must be object", "protocol violation: non-object top-level"

    return obj_any, None, None

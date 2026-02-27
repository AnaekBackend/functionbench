"""Parse model output into structured tool call or parse errors."""

from enum import Enum

from functionbench.core.failure_taxonomy import FailureCode
from functionbench.models.interfaces import ParsedOutput
from functionbench.utils.json_utils import extract_json_from_text, extract_json_strict


class ProtocolMode(str, Enum):
    """How strictly to interpret raw model output as JSON tool calls."""

    JSON_ONLY = "json_only"
    FENCED_JSON = "fenced_json"
    EXTRACT_JSON = "extract_json"


def parse_output(raw: str, protocol_mode: ProtocolMode = ProtocolMode.EXTRACT_JSON) -> ParsedOutput:
    """
    Parse model output according to protocol strictness mode and validate tool-call shape.

    - json_only: raw must be exactly a single JSON object (after stripping whitespace).
    - fenced_json: allow a single fenced JSON code block with no non-whitespace outside;
      if no fence, behave like json_only.
    - extract_json: extract the first JSON object anywhere in the text (backwards compatible).
    """
    errors: list[str] = []
    raw = raw.strip() if raw else ""

    if protocol_mode in (ProtocolMode.JSON_ONLY, ProtocolMode.FENCED_JSON):
        obj, extract_err, protocol_err = extract_json_strict(raw, mode=protocol_mode.value)
        if obj is None:
            if extract_err == "empty input" or extract_err == "no JSON object found":
                errors.append(FailureCode.F8_NOT_JSON)
            elif "JSON" in extract_err:
                errors.append(FailureCode.F9_JSON_PARSE_ERROR)
            else:
                errors.append(FailureCode.F9_JSON_PARSE_ERROR)
            return ParsedOutput(name=None, arguments=None, raw_text=raw, parse_errors=errors)
        if protocol_err:
            errors.append(FailureCode.F10_PROTOCOL_BREAK)
    else:
        obj, extract_err = extract_json_from_text(raw)
        if obj is None:
            if extract_err == "empty input" or extract_err == "no JSON object found":
                errors.append(FailureCode.F8_NOT_JSON)
            elif "JSON" in extract_err:
                errors.append(FailureCode.F9_JSON_PARSE_ERROR)
            else:
                errors.append(FailureCode.F9_JSON_PARSE_ERROR)
            return ParsedOutput(name=None, arguments=None, raw_text=raw, parse_errors=errors)

    # Require "name" (str) and "arguments" (dict)
    name = obj.get("name") if obj is not None else None
    arguments = obj.get("arguments") if obj is not None else None

    if not isinstance(name, str) or name == "":
        errors.append(FailureCode.F10_PROTOCOL_BREAK)
    if not isinstance(arguments, dict):
        errors.append(FailureCode.F10_PROTOCOL_BREAK)

    # In lenient mode, optionally flag lots of prefix text as a protocol break,
    # but only when there are no other parse/protocol errors so far.
    if protocol_mode == ProtocolMode.EXTRACT_JSON and raw and not errors:
        first_brace = raw.find("{")
        if first_brace > 50:  # arbitrary threshold: lots of text before JSON
            errors.append(FailureCode.F10_PROTOCOL_BREAK)

    return ParsedOutput(
        name=name if isinstance(name, str) else None,
        arguments=arguments if isinstance(arguments, dict) else None,
        raw_text=raw,
        parse_errors=errors,
    )

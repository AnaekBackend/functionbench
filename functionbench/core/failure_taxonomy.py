"""Failure codes for structural, protocol, and behavioral evaluation."""

from enum import Enum


class FailureCode(str, Enum):
    """Taxonomy of evaluation failure codes."""

    # Structural
    F1_TOOL_HALLUCINATION = "F1_TOOL_HALLUCINATION"
    F2_WRONG_TOOL = "F2_WRONG_TOOL"
    F3_MISSING_ARGUMENT = "F3_MISSING_ARGUMENT"
    F4_EXTRA_ARGUMENT = "F4_EXTRA_ARGUMENT"
    F5_TYPE_MISMATCH = "F5_TYPE_MISMATCH"
    F6_ENUM_VIOLATION = "F6_ENUM_VIOLATION"
    F7_RANGE_VIOLATION = "F7_RANGE_VIOLATION"
    # Protocol
    F8_NOT_JSON = "F8_NOT_JSON"
    F9_JSON_PARSE_ERROR = "F9_JSON_PARSE_ERROR"
    F10_PROTOCOL_BREAK = "F10_PROTOCOL_BREAK"
    # Behavioral
    F11_SHOULD_CLARIFY_BUT_CALLED_TOOL = "F11_SHOULD_CLARIFY_BUT_CALLED_TOOL"
    F12_SHOULD_CALL_TOOL_BUT_DID_NOT = "F12_SHOULD_CALL_TOOL_BUT_DID_NOT"
    F13_INJECTION_COMPLIANCE = "F13_INJECTION_COMPLIANCE"
    F14_OVERREACH_ON_AMBIGUITY = "F14_OVERREACH_ON_AMBIGUITY"


STRUCTURAL_FAILURES = frozenset(
    {
        FailureCode.F1_TOOL_HALLUCINATION,
        FailureCode.F2_WRONG_TOOL,
        FailureCode.F3_MISSING_ARGUMENT,
        FailureCode.F4_EXTRA_ARGUMENT,
        FailureCode.F5_TYPE_MISMATCH,
        FailureCode.F6_ENUM_VIOLATION,
        FailureCode.F7_RANGE_VIOLATION,
    }
)
PROTOCOL_FAILURES = frozenset(
    {
        FailureCode.F8_NOT_JSON,
        FailureCode.F9_JSON_PARSE_ERROR,
        FailureCode.F10_PROTOCOL_BREAK,
    }
)
BEHAVIORAL_FAILURES = frozenset(
    {
        FailureCode.F11_SHOULD_CLARIFY_BUT_CALLED_TOOL,
        FailureCode.F12_SHOULD_CALL_TOOL_BUT_DID_NOT,
        FailureCode.F13_INJECTION_COMPLIANCE,
        FailureCode.F14_OVERREACH_ON_AMBIGUITY,
    }
)

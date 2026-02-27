"""Tests for output_parser."""

import pytest

from functionbench.core.failure_taxonomy import FailureCode
from functionbench.core.output_parser import ProtocolMode, parse_output


def test_valid_json() -> None:
    raw = '{"name": "set_light", "arguments": {"room": "bedroom", "state": "on", "brightness": 50}}'
    p = parse_output(raw)
    assert p.parse_errors == []
    assert p.name == "set_light"
    assert p.arguments == {"room": "bedroom", "state": "on", "brightness": 50}
    assert p.is_valid_tool_call


def test_markdown_wrapped_json() -> None:
    raw = '```json\n{"name": "set_light", "arguments": {"room": "kitchen"}}\n```'
    p = parse_output(raw)
    assert p.parse_errors == []
    assert p.name == "set_light"
    assert p.arguments == {"room": "kitchen"}


def test_plain_text_no_json() -> None:
    p = parse_output("I'm sorry, I can't do that.")
    assert FailureCode.F8_NOT_JSON in p.parse_errors
    assert p.name is None
    assert p.arguments is None
    assert not p.is_valid_tool_call


def test_malformed_json() -> None:
    p = parse_output('{"name": "set_light", "arguments": ')
    assert FailureCode.F9_JSON_PARSE_ERROR in p.parse_errors
    assert not p.is_valid_tool_call


def test_missing_name() -> None:
    p = parse_output('{"arguments": {"room": "bedroom"}}')
    assert FailureCode.F10_PROTOCOL_BREAK in p.parse_errors
    assert not p.is_valid_tool_call


def test_missing_arguments_key() -> None:
    p = parse_output('{"name": "set_light"}')
    assert FailureCode.F10_PROTOCOL_BREAK in p.parse_errors


def test_arguments_not_dict() -> None:
    p = parse_output('{"name": "set_light", "arguments": "invalid"}')
    assert FailureCode.F10_PROTOCOL_BREAK in p.parse_errors


def test_empty_input() -> None:
    p = parse_output("")
    assert FailureCode.F8_NOT_JSON in p.parse_errors or FailureCode.F9_JSON_PARSE_ERROR in p.parse_errors


def test_json_only_rejects_prefix_text() -> None:
    raw = 'prefix\n{"name": "set_light", "arguments": {"room": "bedroom"}}'
    p = parse_output(raw, protocol_mode=ProtocolMode.JSON_ONLY)
    assert FailureCode.F8_NOT_JSON in p.parse_errors or FailureCode.F9_JSON_PARSE_ERROR in p.parse_errors


def test_fenced_json_strict_mode() -> None:
    raw = '```json\n{"name": "set_light", "arguments": {"room": "kitchen"}}\n```'
    p = parse_output(raw, protocol_mode=ProtocolMode.FENCED_JSON)
    assert p.parse_errors == []
    assert p.name == "set_light"
    assert p.arguments == {"room": "kitchen"}


def test_fenced_json_with_suffix_protocol_break() -> None:
    raw = '```json\n{"name": "set_light", "arguments": {"room": "kitchen"}}\n``` extra'
    p = parse_output(raw, protocol_mode=ProtocolMode.FENCED_JSON)
    assert FailureCode.F10_PROTOCOL_BREAK in p.parse_errors

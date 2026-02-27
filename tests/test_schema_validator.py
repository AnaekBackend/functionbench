"""Tests for schema_validator."""

import pytest

from functionbench.core.failure_taxonomy import FailureCode
from functionbench.core.schema_validator import validate_tool_call
from functionbench.models.interfaces import ToolSchema


@pytest.fixture
def schema() -> ToolSchema:
    return ToolSchema(
        arguments={
            "room": ["bedroom", "living_room", "kitchen"],
            "state": ["on", "off"],
            "brightness": {"type": "int", "min": 0, "max": 100},
        },
        required=["room", "state", "brightness"],
    )


def test_valid_call(schema: ToolSchema) -> None:
    assert validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on", "brightness": 50},
        schema,
    ) == []


def test_missing_argument(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on"},
        schema,
    )
    assert FailureCode.F3_MISSING_ARGUMENT in failures


def test_extra_argument(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on", "brightness": 50, "extra": 1},
        schema,
    )
    assert FailureCode.F4_EXTRA_ARGUMENT in failures


def test_enum_violation(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "garage", "state": "on", "brightness": 50},
        schema,
    )
    assert FailureCode.F6_ENUM_VIOLATION in failures


def test_type_mismatch(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on", "brightness": "high"},
        schema,
    )
    assert FailureCode.F5_TYPE_MISMATCH in failures


def test_range_violation_low(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on", "brightness": -1},
        schema,
    )
    assert FailureCode.F7_RANGE_VIOLATION in failures


def test_range_violation_high(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "bedroom", "state": "on", "brightness": 101},
        schema,
    )
    assert FailureCode.F7_RANGE_VIOLATION in failures


def test_multiple_failures(schema: ToolSchema) -> None:
    failures = validate_tool_call(
        "set_light",
        {"room": "garage", "brightness": 200},
        schema,
    )
    assert FailureCode.F3_MISSING_ARGUMENT in failures
    assert FailureCode.F6_ENUM_VIOLATION in failures
    assert FailureCode.F7_RANGE_VIOLATION in failures

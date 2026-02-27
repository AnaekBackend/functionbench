"""Pytest fixtures for FunctionBench tests."""

import pytest

from functionbench.models.interfaces import ToolSchema


@pytest.fixture
def sample_schema() -> ToolSchema:
    """Tool schema matching spec example: set_light with room, state, brightness."""
    return ToolSchema(
        arguments={
            "room": ["bedroom", "living_room", "kitchen"],
            "state": ["on", "off"],
            "brightness": {"type": "int", "min": 0, "max": 100},
        },
        required=["room", "state", "brightness"],
    )

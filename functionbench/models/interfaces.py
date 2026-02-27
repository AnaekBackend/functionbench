"""Data models and type aliases for the evaluation pipeline."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


# Model callable: input string -> output string
ModelCallable = Callable[[str], str]


class ArgumentTypeDef(BaseModel):
    """Numeric/typed argument with optional range."""

    type: str  # "int", "float", etc.
    min: int | float | None = None
    max: int | float | None = None


# Schema: each argument is either enum (list of allowed values) or typed with range
ToolArgumentsSchema = dict[str, list[Any] | dict[str, Any]]


class ToolSchema(BaseModel):
    """Schema for a single tool."""

    arguments: dict[str, list[Any] | dict[str, Any]] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)

    def get_required(self) -> list[str]:
        return self.required

    def get_argument_def(self, name: str) -> list[Any] | dict[str, Any] | None:
        return self.arguments.get(name)


class DatasetCase(BaseModel):
    """Single evaluation case from dataset.jsonl."""

    id: str
    input: str
    expected_behavior: str  # call_tool | clarification_required | reject
    category: str
    expected_tool: str | None = None
    expected_arguments: dict[str, Any] | None = None


@dataclass
class ParsedOutput:
    """Result of parsing model output."""

    name: str | None  # tool name
    arguments: dict[str, Any] | None
    raw_text: str
    parse_errors: list[str]  # failure codes or messages from parser

    @property
    def is_valid_tool_call(self) -> bool:
        return self.name is not None and self.arguments is not None and not self.parse_errors


@dataclass
class EvalResult:
    """Result of evaluating one case."""

    case_id: str
    passed: bool
    failures: list[str]  # FailureCode values as strings

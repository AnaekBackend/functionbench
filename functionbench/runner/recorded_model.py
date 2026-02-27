"""Recorded response model for testing: returns pre-recorded outputs by input."""

import json
from pathlib import Path

from functionbench.models.interfaces import ModelCallable


def load_recorded_responses(path: str | Path) -> dict[str, str]:
    """Load a JSONL of {input, output} into a mapping input -> JSON string of output."""
    path = Path(path)
    mapping: dict[str, str] = {}
    for line in path.read_text().strip().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        inp = row.get("input", "")
        out = row.get("output")
        mapping[inp] = json.dumps(out) if out is not None else ""
    return mapping


def recorded_model(responses: dict[str, str] | None = None, path: str | Path | None = None) -> ModelCallable:
    """
    Return a model callable that looks up input in responses and returns the stored output.
    Either pass responses dict directly or path to a JSONL file with "input" and "output" keys.
    """
    if responses is None:
        if path is None:
            raise ValueError("Provide either responses or path")
        responses = load_recorded_responses(path)

    def _call(inp: str) -> str:
        return responses.get(inp, "{}")

    return _call


# Default path: data/recorded_outputs.jsonl under repo root (when run from repo)
_RECORDED_RESPONSES: dict[str, str] | None = None


def _get_responses() -> dict[str, str]:
    global _RECORDED_RESPONSES
    if _RECORDED_RESPONSES is None:
        base = Path(__file__).resolve().parent.parent.parent
        path = base / "data" / "recorded_outputs.jsonl"
        if not path.exists():
            path = Path.cwd() / "data" / "recorded_outputs.jsonl"
        _RECORDED_RESPONSES = load_recorded_responses(path)
    return _RECORDED_RESPONSES


def recorded_model_from_data(input_text: str) -> str:
    """
    Model callable for CLI: --model functionbench.runner.recorded_model:recorded_model_from_data
    Returns pre-recorded JSON output for the given input (from data/recorded_outputs.jsonl).
    """
    return _get_responses().get(input_text, "{}")

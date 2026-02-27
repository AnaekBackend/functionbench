"""Load and validate tool schemas from tools.json."""

import json
from pathlib import Path

from functionbench.models.interfaces import ToolSchema


def load_tools(path: str | Path) -> dict[str, ToolSchema]:
    """
    Load tools.json and return a dict mapping tool name -> ToolSchema.
    Validates that each tool has 'arguments' and 'required' keys.
    """
    path = Path(path)
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError("tools.json must be a JSON object")

    result: dict[str, ToolSchema] = {}
    for name, defn in raw.items():
        if not isinstance(defn, dict):
            raise ValueError(f"Tool '{name}' must be an object")
        if "arguments" not in defn:
            raise ValueError(f"Tool '{name}' missing 'arguments'")
        if "required" not in defn:
            raise ValueError(f"Tool '{name}' missing 'required'")
        result[name] = ToolSchema(arguments=defn["arguments"], required=defn["required"])
    return result

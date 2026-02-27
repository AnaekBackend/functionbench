"""Validate a tool call against a tool schema."""

from functionbench.core.failure_taxonomy import FailureCode
from functionbench.models.interfaces import ToolSchema


def validate_tool_call(name: str, arguments: dict, schema: ToolSchema) -> list[FailureCode]:
    """
    Validate tool name and arguments against schema.
    Returns list of failure codes (F3–F7). Does not check tool name vs expected (evaluator does that).
    """
    failures: list[FailureCode] = []
    required = set(schema.get_required())
    arg_defs = schema.arguments
    allowed_keys = set(arg_defs.keys())

    # F3: missing required
    given_keys = set(arguments.keys())
    for r in required:
        if r not in given_keys:
            failures.append(FailureCode.F3_MISSING_ARGUMENT)

    # F4: extra argument
    for k in given_keys:
        if k not in allowed_keys:
            failures.append(FailureCode.F4_EXTRA_ARGUMENT)

    # F5, F6, F7: per-argument type, enum, range
    for key, value in arguments.items():
        if key not in arg_defs:
            continue
        defn = arg_defs[key]
        if isinstance(defn, list):
            # enum
            if value not in defn:
                failures.append(FailureCode.F6_ENUM_VIOLATION)
        elif isinstance(defn, dict):
            # typed with optional min/max
            expected_type = defn.get("type", "str")
            if expected_type == "int":
                if not isinstance(value, int):
                    failures.append(FailureCode.F5_TYPE_MISMATCH)
                else:
                    lo = defn.get("min")
                    hi = defn.get("max")
                    if lo is not None and value < lo:
                        failures.append(FailureCode.F7_RANGE_VIOLATION)
                    if hi is not None and value > hi:
                        failures.append(FailureCode.F7_RANGE_VIOLATION)
            elif expected_type == "float":
                if not isinstance(value, (int, float)):
                    failures.append(FailureCode.F5_TYPE_MISMATCH)
                else:
                    v = float(value)
                    lo = defn.get("min")
                    hi = defn.get("max")
                    if lo is not None and v < lo:
                        failures.append(FailureCode.F7_RANGE_VIOLATION)
                    if hi is not None and v > hi:
                        failures.append(FailureCode.F7_RANGE_VIOLATION)
            # else str or unknown: no type/range check for v0.1

    return failures

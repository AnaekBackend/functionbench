"""Tests for metrics computation and failure-code normalization."""

from functionbench.core.scoring import compute_metrics
from functionbench.models.interfaces import DatasetCase, EvalResult


def test_compute_metrics_normalizes_legacy_failure_strings() -> None:
    cases = [
        DatasetCase(
            id="c1",
            input="x",
            expected_behavior="call_tool",
            category="clean_valid",
            expected_tool="t",
            expected_arguments={},
        ),
        DatasetCase(
            id="c2",
            input="y",
            expected_behavior="clarification_required",
            category="boundary_test",
            expected_tool=None,
            expected_arguments=None,
        ),
    ]
    results = [
        EvalResult(
            case_id="c1",
            passed=False,
            failures=["FailureCode.F8_NOT_JSON"],
        ),
        EvalResult(
            case_id="c2",
            passed=False,
            failures=["FailureCode.F1_TOOL_HALLUCINATION"],
        ),
    ]

    metrics = compute_metrics(results, cases, protocol_mode="json_only")

    assert metrics.failure_counts["F8_NOT_JSON"] == 1
    assert metrics.failure_counts["F1_TOOL_HALLUCINATION"] == 1
    assert metrics.json_valid_count == 1
    assert metrics.strict_protocol_pass_count == 1

"""Tests for console and report output."""

import io
from contextlib import redirect_stdout

from functionbench.core.report import print_console_report
from functionbench.core.scoring import CategoryMetrics, Metrics


def _sample_metrics() -> Metrics:
    return Metrics(
        total_cases=10,
        exact_match_count=8,
        json_valid_count=9,
        strict_protocol_pass_count=7,
        protocol_mode="json_only",
        failure_counts={"F1_TOOL_HALLUCINATION": 2},
        by_category={
            "clean_valid": CategoryMetrics(
                category="clean_valid",
                total=6,
                exact_match=6,
                json_valid=6,
                failure_counts={},
            ),
            "injection_test": CategoryMetrics(
                category="injection_test",
                total=4,
                exact_match=2,
                json_valid=4,
                failure_counts={"F1_TOOL_HALLUCINATION": 2},
            ),
        },
    )


def test_print_console_report_contains_expected_tokens() -> None:
    """print_console_report outputs key tokens and does not crash."""
    metrics = _sample_metrics()
    out = io.StringIO()
    with redirect_stdout(out):
        print_console_report(metrics, run_name=None, timestamp=False)
    text = out.getvalue()
    assert "FunctionBench" in text
    assert "Protocol mode" in text
    assert "Exact match" in text
    assert "Total" in text
    assert "clean_valid" in text
    assert "injection_test" in text
    assert "F1 Tool hallucination" in text or "F1_TOOL_HALLUCINATION" in text


def test_print_console_report_with_run_name() -> None:
    """run_name appears in header when provided."""
    metrics = _sample_metrics()
    out = io.StringIO()
    with redirect_stdout(out):
        print_console_report(metrics, run_name="lmstudio", timestamp=False)
    assert "lmstudio" in out.getvalue()


def test_print_console_report_no_failures() -> None:
    """Empty failure_counts does not crash; no failure table section."""
    metrics = Metrics(
        total_cases=5,
        exact_match_count=5,
        json_valid_count=5,
        failure_counts={},
        by_category={
            "clean": CategoryMetrics("clean", total=5, exact_match=5, json_valid=5),
        },
    )
    out = io.StringIO()
    with redirect_stdout(out):
        print_console_report(metrics, timestamp=False)
    text = out.getvalue()
    assert "FunctionBench" in text
    assert "5" in text

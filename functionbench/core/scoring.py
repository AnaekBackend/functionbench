"""Compute aggregate and per-category metrics from evaluation results."""

from dataclasses import dataclass, field

from functionbench.core.failure_taxonomy import FailureCode
from functionbench.models.interfaces import DatasetCase, EvalResult


@dataclass
class CategoryMetrics:
    """Metrics for a single category."""

    category: str
    total: int
    exact_match: int
    json_valid: int
    failure_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class Metrics:
    """Aggregate and per-category metrics."""

    total_cases: int
    exact_match_count: int
    json_valid_count: int
    strict_protocol_pass_count: int = 0
    protocol_mode: str | None = None
    failure_counts: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, CategoryMetrics] = field(default_factory=dict)

    @property
    def exact_match_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.exact_match_count / self.total_cases

    @property
    def json_validity_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.json_valid_count / self.total_cases

    @property
    def strict_protocol_pass_rate(self) -> float:
        """
        Fraction of all cases that satisfied strict protocol rules on call_tool cases.
        Defined as: for call_tool cases, no F8/F9/F10 failures; other cases do not
        contribute protocol failures and are counted as passes.
        """
        if self.total_cases == 0:
            return 0.0
        return self.strict_protocol_pass_count / self.total_cases

    def failure_rate(self, code: str) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.failure_counts.get(code, 0) / self.total_cases


def compute_metrics(
    results: list[EvalResult],
    cases: list[DatasetCase],
    protocol_mode: str | None = None,
) -> Metrics:
    """Compute global and per-category metrics from results and original cases."""
    case_by_id = {c.id: c for c in cases}
    total = len(results)
    exact_match_count = sum(1 for r in results if r.passed)
    json_valid_count = sum(
        1
        for r in results
        if not any(f in (FailureCode.F8_NOT_JSON, FailureCode.F9_JSON_PARSE_ERROR) for f in r.failures)
    )

    # Strict protocol pass: no F8/F9/F10 failures on call_tool cases.
    case_by_id = {c.id: c for c in cases}
    strict_protocol_pass_count = 0
    for r in results:
        case = case_by_id.get(r.case_id)
        if case and case.expected_behavior == "call_tool":
            if not any(
                f in (FailureCode.F8_NOT_JSON, FailureCode.F9_JSON_PARSE_ERROR, FailureCode.F10_PROTOCOL_BREAK)
                for f in r.failures
            ):
                strict_protocol_pass_count += 1
        else:
            # Non-call_tool behaviors are not subject to tool-calling protocol rules.
            strict_protocol_pass_count += 1

    failure_counts: dict[str, int] = {}
    for r in results:
        for f in r.failures:
            failure_counts[f] = failure_counts.get(f, 0) + 1

    by_category: dict[str, CategoryMetrics] = {}
    for r in results:
        case = case_by_id.get(r.case_id)
        cat = case.category if case else "unknown"
        if cat not in by_category:
            by_category[cat] = CategoryMetrics(category=cat, total=0, exact_match=0, json_valid=0)
        cm = by_category[cat]
        cm.total += 1
        if r.passed:
            cm.exact_match += 1
        if not any(f in (FailureCode.F8_NOT_JSON, FailureCode.F9_JSON_PARSE_ERROR) for f in r.failures):
            cm.json_valid += 1
        for f in r.failures:
            cm.failure_counts[f] = cm.failure_counts.get(f, 0) + 1

    return Metrics(
        total_cases=total,
        exact_match_count=exact_match_count,
        json_valid_count=json_valid_count,
        strict_protocol_pass_count=strict_protocol_pass_count,
        protocol_mode=protocol_mode,
        failure_counts=failure_counts,
        by_category=by_category,
    )

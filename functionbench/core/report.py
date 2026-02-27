"""Console, JSON, and Markdown reporting for evaluation metrics."""

import json
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from functionbench.core.scoring import CategoryMetrics, Metrics

# Short labels for failure codes (for table column)
FAILURE_LABELS = {
    "F1_TOOL_HALLUCINATION": "F1 Tool hallucination",
    "F2_WRONG_TOOL": "F2 Wrong tool",
    "F3_MISSING_ARGUMENT": "F3 Missing argument",
    "F4_EXTRA_ARGUMENT": "F4 Extra argument",
    "F5_TYPE_MISMATCH": "F5 Type mismatch",
    "F6_ENUM_VIOLATION": "F6 Enum violation",
    "F7_RANGE_VIOLATION": "F7 Range violation",
    "F8_NOT_JSON": "F8 Not JSON",
    "F9_JSON_PARSE_ERROR": "F9 JSON parse error",
    "F10_PROTOCOL_BREAK": "F10 Protocol break",
    "F11_SHOULD_CLARIFY_BUT_CALLED_TOOL": "F11 Should clarify but called tool",
    "F12_SHOULD_CALL_TOOL_BUT_DID_NOT": "F12 Should call tool but did not",
    "F13_INJECTION_COMPLIANCE": "F13 Injection compliance",
    "F14_OVERREACH_ON_AMBIGUITY": "F14 Overreach on ambiguity",
}


def _console() -> Console:
    """Console that respects NO_COLOR and uses stdout (for piping)."""
    no_color = os.environ.get("NO_COLOR", "").strip().lower() in ("1", "true", "yes")
    return Console(force_terminal=None, no_color=no_color)


def print_console_report(
    metrics: Metrics,
    run_name: str | None = None,
    timestamp: bool = True,
) -> None:
    """Print formatted summary with rich tables to stdout."""
    console = _console()
    total = metrics.total_cases
    exact_pct = 100.0 * metrics.exact_match_rate
    json_pct = 100.0 * metrics.json_validity_rate
    strict_pct = 100.0 * metrics.strict_protocol_pass_rate

    # Header
    parts = ["FunctionBench"]
    if run_name:
        parts.append(run_name)
    if timestamp:
        parts.append(datetime.now().strftime("%b %d %H:%M"))
    console.print("  ".join(parts), style="bold")
    if metrics.protocol_mode:
        console.print(f"[dim]Protocol mode:[/dim] {metrics.protocol_mode}")
    console.print()

    # Summary table
    summary = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    summary.add_column("Total", justify="right")
    summary.add_column("Exact match", justify="right")
    summary.add_column("JSON valid", justify="right")
    summary.add_column("Strict protocol", justify="right")
    summary.add_row(str(total), f"{exact_pct:.1f}%", f"{json_pct:.1f}%", f"{strict_pct:.1f}%")
    console.print(summary)
    console.print()

    # Per-category table
    cat_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    cat_table.add_column("#", justify="right", style="dim")
    cat_table.add_column("Category", justify="left")
    cat_table.add_column("Total", justify="right")
    cat_table.add_column("Exact", justify="right")
    cat_table.add_column("Exact%", justify="right")
    cat_table.add_column("JSON%", justify="right")
    for i, cat in enumerate(sorted(metrics.by_category.keys()), 1):
        cm = metrics.by_category[cat]
        em_pct = 100.0 * cm.exact_match / cm.total if cm.total else 0
        jv_pct = 100.0 * cm.json_valid / cm.total if cm.total else 0
        cat_table.add_row(
            str(i),
            cat,
            str(cm.total),
            str(cm.exact_match),
            f"{em_pct:.1f}%",
            f"{jv_pct:.1f}%",
        )
    console.print(cat_table)
    console.print()

    # Failure breakdown (only rows with count > 0)
    if metrics.failure_counts:
        fail_table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        fail_table.add_column("Failure", justify="left")
        fail_table.add_column("Count", justify="right")
        fail_table.add_column("Rate", justify="right")
        use_color = console.is_terminal and not os.environ.get("NO_COLOR", "").strip().lower() in ("1", "true", "yes")
        for code in sorted(metrics.failure_counts.keys()):
            count = metrics.failure_counts[code]
            pct = 100.0 * count / total if total else 0
            label = FAILURE_LABELS.get(code, code.replace("_", " ").title())
            rate_str = f"{pct:.1f}%"
            if use_color:
                if pct == 0:
                    rate_str = f"[green]{rate_str}[/green]"
                elif pct >= 10:
                    rate_str = f"[red]{rate_str}[/red]"
            fail_table.add_row(label, str(count), rate_str)
        console.print(fail_table)


def _metrics_to_dict(metrics: Metrics) -> dict:
    """Convert Metrics and nested CategoryMetrics to JSON-serializable dict."""
    return {
        "total_cases": metrics.total_cases,
        "exact_match_count": metrics.exact_match_count,
        "exact_match_rate": metrics.exact_match_rate,
        "json_valid_count": metrics.json_valid_count,
        "json_validity_rate": metrics.json_validity_rate,
        "strict_protocol_pass_count": metrics.strict_protocol_pass_count,
        "strict_protocol_pass_rate": metrics.strict_protocol_pass_rate,
        "protocol_mode": metrics.protocol_mode,
        "failure_counts": metrics.failure_counts,
        "by_category": {
            cat: {
                "category": cm.category,
                "total": cm.total,
                "exact_match": cm.exact_match,
                "exact_match_rate": cm.exact_match / cm.total if cm.total else 0,
                "json_valid": cm.json_valid,
                "json_validity_rate": cm.json_valid / cm.total if cm.total else 0,
                "failure_counts": cm.failure_counts,
            }
            for cat, cm in metrics.by_category.items()
        },
    }


def write_json_report(metrics: Metrics, path: str | Path) -> None:
    """Write structured metrics to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_metrics_to_dict(metrics), indent=2))


def write_markdown_report(metrics: Metrics, path: str | Path) -> None:
    """Write a markdown summary suitable for README or docs."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    total = metrics.total_cases
    exact_pct = 100.0 * metrics.exact_match_rate
    json_pct = 100.0 * metrics.json_validity_rate
    strict_pct = 100.0 * metrics.strict_protocol_pass_rate
    mode = metrics.protocol_mode or "unknown"
    lines = [
        "# FunctionBench Report",
        "",
        "## Summary",
        "",
        f"- **Total cases:** {total}",
        f"- **Exact match:** {exact_pct:.1f}%",
        f"- **JSON validity:** {json_pct:.1f}%",
        f"- **Protocol mode:** {mode}",
        f"- **Strict protocol pass:** {strict_pct:.1f}%",
        "",
        "## Failure breakdown",
        "",
        "| Failure | Count | Rate |",
        "|---------|-------|------|",
    ]
    for code in sorted(metrics.failure_counts.keys()):
        count = metrics.failure_counts[code]
        pct = 100.0 * count / total if total else 0
        lines.append(f"| {code} | {count} | {pct:.1f}% |")
    lines.extend(["", "## Per-category", ""])
    for cat in sorted(metrics.by_category.keys()):
        cm = metrics.by_category[cat]
        em_rate = 100.0 * cm.exact_match / cm.total if cm.total else 0
        lines.append(f"- **{cat}**: {cm.exact_match}/{cm.total} exact match ({em_rate:.1f}%)")
    path.write_text("\n".join(lines))

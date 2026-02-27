"""CLI entry point for running FunctionBench evaluation."""

import argparse
import importlib
import json
import sys
from pathlib import Path

from functionbench.core.evaluator import evaluate_case
from functionbench.core.report import print_console_report, write_json_report
from functionbench.core.schema_loader import load_tools
from functionbench.core.output_parser import ProtocolMode, parse_output
from functionbench.core.scoring import compute_metrics
from functionbench.models.interfaces import DatasetCase, EvalResult, ModelCallable


def resolve_model_callable(dotted_path: str) -> ModelCallable:
    """Resolve 'module.path:callable_name' to a callable."""
    if ":" not in dotted_path:
        raise ValueError("Model must be specified as 'module.path:callable_name'")
    mod_path, attr = dotted_path.rsplit(":", 1)
    module = importlib.import_module(mod_path)
    if not hasattr(module, attr):
        raise AttributeError(f"Module {mod_path} has no attribute {attr}")
    callable_obj = getattr(module, attr)
    if not callable(callable_obj):
        raise TypeError(f"{mod_path}.{attr} is not callable")
    return callable_obj


def load_dataset(path: str | Path) -> list[DatasetCase]:
    """Load dataset from JSONL file."""
    path = Path(path)
    cases = []
    for line in path.read_text().strip().splitlines():
        line = line.strip()
        if not line:
            continue
        cases.append(DatasetCase.model_validate(json.loads(line)))
    return cases


def run_evaluation(
    dataset_path: str | Path,
    tools_path: str | Path,
    model: ModelCallable,
    protocol_mode: ProtocolMode = ProtocolMode.EXTRACT_JSON,
    progress_file: object | None = None,
) -> tuple[list[EvalResult], list[DatasetCase], dict, list[dict]]:
    """Load tools and dataset, run model on each case, evaluate. Returns results, cases, tools, and detailed rows for logging."""
    tools = load_tools(tools_path)
    cases = load_dataset(dataset_path)
    total = len(cases)
    results: list[EvalResult] = []
    detailed: list[dict] = []
    out = progress_file if progress_file is not None else sys.stderr
    is_tty = getattr(out, "isatty", lambda: False)()

    for i, case in enumerate(cases, 1):
        raw_output = model(case.input)
        parsed = parse_output(raw_output, protocol_mode=protocol_mode)
        result = evaluate_case(parsed, case, tools)
        results.append(result)
        if is_tty:
            print(f"\rEvaluating {i}/{total} ({case.id})   ", end="", file=out, flush=True)
        elif i % max(1, total // 20) == 0 or i == total:
            print(f"Evaluating {i}/{total} ({case.id})", file=out, flush=True)
        detailed.append({
            "case_id": case.id,
            "input": case.input,
            "expected_behavior": case.expected_behavior,
            "category": case.category,
            "expected_tool": case.expected_tool,
            "expected_arguments": case.expected_arguments,
            "raw_output": raw_output,
            "parsed_name": parsed.name,
            "parsed_arguments": parsed.arguments,
            "passed": result.passed,
            "failures": result.failures,
        })
    if is_tty:
        print(file=out, flush=True)
    return results, cases, tools, detailed


def main() -> int:
    parser = argparse.ArgumentParser(description="FunctionBench evaluation runner")
    parser.add_argument("--dataset", required=True, help="Path to dataset.jsonl")
    parser.add_argument("--tools", required=True, help="Path to tools.json")
    parser.add_argument("--model", required=True, help="Dotted path to model callable, e.g. mypackage.models:caller")
    parser.add_argument("--output", default=None, help="Path to write JSON report (overridden by --output-dir + --run-name)")
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Directory for reports; use with --run-name to write DIR/RUN_NAME/report.json (and detailed.jsonl if --detailed)",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        metavar="NAME",
        help="Label for this run; with --output-dir writes to DIR/NAME/. Use e.g. model name for multi-model evals.",
    )
    parser.add_argument(
        "--detailed",
        nargs="?",
        default=None,
        const="",
        metavar="PATH",
        help="Write per-case JSONL. If PATH given, use it; else with --output-dir + --run-name use DIR/NAME/detailed.jsonl",
    )
    parser.add_argument(
        "--protocol",
        choices=[m.value for m in ProtocolMode],
        default=ProtocolMode.EXTRACT_JSON.value,
        help="Protocol strictness for parsing model outputs: json_only | fenced_json | extract_json (default: extract_json)",
    )
    args = parser.parse_args()

    # Resolve report and detailed paths
    if args.output_dir and args.run_name:
        run_dir = Path(args.output_dir) / args.run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "report.json"
        if args.detailed is not None:
            detailed_path = Path(args.detailed) if args.detailed else run_dir / "detailed.jsonl"
        else:
            detailed_path = None
    else:
        report_path = Path(args.output) if args.output else None
        if args.detailed is not None:
            detailed_path = Path(args.detailed) if args.detailed else Path("detailed.jsonl")
        else:
            detailed_path = None
        if args.output_dir and not args.run_name:
            print("Warning: --output-dir is ignored without --run-name", file=sys.stderr)
        if args.run_name and not args.output_dir:
            print("Warning: --run-name is ignored without --output-dir", file=sys.stderr)

    try:
        model_fn = resolve_model_callable(args.model)
    except Exception as e:
        print(f"Failed to load model: {e}", file=sys.stderr)
        return 1

    protocol_mode = ProtocolMode(args.protocol)

    try:
        results, cases, _, detailed_rows = run_evaluation(
            args.dataset,
            args.tools,
            model_fn,
            protocol_mode=protocol_mode,
        )
    except FileNotFoundError as e:
        print(f"File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Evaluation error: {e}", file=sys.stderr)
        return 1

    metrics = compute_metrics(results, cases, protocol_mode=protocol_mode.value)
    print_console_report(metrics, run_name=args.run_name)
    if report_path:
        write_json_report(metrics, report_path)
        print(f"Report: {report_path}", file=sys.stderr)
    if detailed_path:
        detailed_path.parent.mkdir(parents=True, exist_ok=True)
        with open(detailed_path, "w") as f:
            for row in detailed_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Detailed: {detailed_path} ({len(detailed_rows)} cases)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

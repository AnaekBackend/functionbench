# FunctionBench

Reliability benchmark for tool-using LLMs.

## Installation

From GitHub:

```bash
pip install "git+https://github.com/AnaekBackend/functionbench.git"
```

With `uv`:

```bash
uv add "functionbench @ git+https://github.com/AnaekBackend/functionbench.git"
```

From a local clone (editable):

```bash
pip install -e /path/to/functionbench
```

## Running evaluations

You currently have two supported ways to run evaluations.

### Method 1: from your own eval project (GitHub dependency, recommended)

1. Create a project with your model callable, `data/dataset.jsonl`, and `data/tools.json`.
1. Add FunctionBench from GitHub:

```bash
# uv
uv add "functionbench @ git+https://github.com/AnaekBackend/functionbench.git"

# or pip
pip install "git+https://github.com/AnaekBackend/functionbench.git"
```

1. From your project root, run:

```bash
uv run fb-eval \
  --dataset data/dataset.jsonl \
  --tools data/tools.json \
  --model lmstudio_model:lmstudio_callable \
  --output reports/report.json \
  --protocol extract_json
```

Your project root is on the module path, so `--model lmstudio_model:lmstudio_callable` resolves to your local `lmstudio_model.py`.

### Method 2: from a local clone

If you cloned this repo locally, either run the CLI from the clone directly:

```bash
uv run --directory /path/to/functionbench fb-eval \
  --dataset /path/to/your/data/dataset.jsonl \
  --tools /path/to/your/data/tools.json \
  --model your_model_module:your_callable \
  --output /path/to/your/reports/report.json \
  --protocol extract_json
```

Or install editable from the clone:

```bash
pip install -e /path/to/functionbench
```

Then run `fb-eval` from your eval project normally.

### LM Studio model callable (`lmstudio_model.py`)

This repo now includes a ready-to-use callable at `lmstudio_model.py`:

- Callable name: `lmstudio_callable`
- Signature: `(input: str) -> str`
- Transport: OpenAI-compatible LM Studio endpoint at `/v1/chat/completions`

It reads these environment variables:

- `FUNCTIONBENCH_LMSTUDIO_URL` (default: `http://127.0.0.1:1234`)
- `FUNCTIONBENCH_LMSTUDIO_MODEL` (default: `lm-studio`)
- `FUNCTIONBENCH_TOOLS_JSON` (optional): path to `tools.json`; when set, tool schema is injected into the system prompt so the model uses exact tool names/argument keys.

Example:

```bash
export FUNCTIONBENCH_LMSTUDIO_URL="http://127.0.0.1:1234"
export FUNCTIONBENCH_LMSTUDIO_MODEL="qwen2.5-7b-instruct"
export FUNCTIONBENCH_TOOLS_JSON="data/tools.json"

uv run fb-eval \
  --dataset data/sample_dataset.jsonl \
  --tools data/tools.json \
  --model lmstudio_model:lmstudio_callable \
  --output reports/lmstudio_report.json \
  --protocol extract_json
```

> Note: `lmstudio_model.py` uses `requests`, so install it in your evaluation environment if needed (`pip install requests`).

### CLI flags

- **`--dataset`**: path to a JSONL dataset.
- **`--tools`**: path to `tools.json`.
- **`--model`**: dotted path to a callable: `module.path:callable_name` (must accept `str` and return `str`).
- **`--output`**: write aggregate JSON report to a path (optional; overridden by `--output-dir` + `--run-name`).
- **`--output-dir` + `--run-name`**: write `report.json` (and optionally `detailed.jsonl`) into `DIR/RUN_NAME/`.
- **`--detailed [PATH]`**: write per-case JSONL (if PATH omitted, uses `DIR/RUN_NAME/detailed.jsonl` when `--output-dir` + `--run-name` are set).
- **`--protocol`**: protocol strictness for parsing model outputs: `json_only | fenced_json | extract_json` (default: `extract_json`).

### Example: run with bundled smoke-test data

This repo includes a tiny smoke-test dataset plus a recorded-response model so you can verify everything works without connecting to a real model:

```bash
uv run fb-eval \
  --dataset data/dataset.jsonl \
  --tools data/tools.json \
  --model functionbench.runner.recorded_model:recorded_model_from_data \
  --output-dir reports \
  --run-name demo \
  --detailed \
  --protocol extract_json
```

This writes:

- `reports/demo/report.json` (aggregate metrics)
- `reports/demo/detailed.jsonl` (per-case raw output + parsed fields + failures)

### Sample dataset

The repo ships multiple smart-home style datasets under `data/`:

- `data/tools.json`: tool schemas for `set_light`, `set_fan`, `set_temperature`, and `ask_clarify`.
- `data/dataset.jsonl`: 13-case smoke-test dataset used for quick deterministic checks.
- `data/sample_dataset.jsonl`: larger benchmark-oriented dataset showing practical category coverage (`clean_valid`, `boundary_test`, `missing_argument`, `ambiguity_test`, `range_violation_probe`, `tool_confusion_probe`, `injection_test`, `extra_argument_probe`) and normalization behavior.
- `data/recorded_outputs.jsonl`: pre-recorded outputs used by `recorded_model_from_data` for a deterministic demo run.

Use `data/sample_dataset.jsonl` as the primary guide for creating domain-specific benchmark datasets and `data/tools.json` as the matching tool-schema template.

### Example metrics (dummy)

Console summary (illustrative):

```text
FunctionBench  demo  Feb 27 14:19

  Total    Exact match    JSON valid    Strict protocol
    570          19.8%         99.6%              92.1%

Protocol mode: extract_json
```

Report JSON excerpt (illustrative):

```json
{
  "total_cases": 570,
  "exact_match_rate": 0.198,
  "json_validity_rate": 0.996,
  "strict_protocol_pass_rate": 0.921,
  "protocol_mode": "extract_json",
  "failure_counts": {
    "F1_TOOL_HALLUCINATION": 358,
    "F9_JSON_PARSE_ERROR": 2
  }
}
```

### Protocol modes

FunctionBench supports configurable protocol strictness for parsing model outputs:

- `extract_json` (default): extract the first valid JSON object anywhere in the text; tolerate prefix/suffix text.
- `fenced_json`: require a single fenced JSON code block (for example, ` ```json` … ` ``` ` or ` ``` ` … ` ``` `), with no non-whitespace outside; if no fence, behaves like `json_only`.
- `json_only`: require the entire output (after stripping whitespace) to be a single valid JSON object.

Use `--protocol` to select a mode. The report includes the protocol mode and a strict protocol pass rate based on `F8_NOT_JSON`, `F9_JSON_PARSE_ERROR`, and `F10_PROTOCOL_BREAK`.

## Running tests (contributors)

```bash
uv run pytest
```

# LangSmith CLI Command Reference

## Command Tree

```
langsmith
├── project
│   └── list              List tracing projects
├── trace
│   ├── list              List traces (filters apply to root run)
│   ├── get               Get single trace with full run hierarchy
│   └── export            Export traces to JSONL (one file per trace)
├── run
│   ├── list              List runs (flat, filters apply to any run)
│   ├── get               Get single run by ID
│   └── export            Export runs to single JSONL file
├── dataset
│   ├── list / get / create / delete
│   ├── export            Export dataset to file
│   └── upload            Upload local JSON as dataset
├── example
│   ├── list / create / delete
├── evaluator
│   ├── list / upload / delete
├── experiment
│   ├── list / get
├── thread
│   ├── list / get
└── --help
```

## Traces vs Runs

| | `trace *` | `run *` |
|---|---|---|
| Returns | Full hierarchy (tree) | Flat list |
| Filters apply to | Root run only | Any matching run |
| `--run-type` filter | Not available | Available (llm, chain, tool, retriever) |
| Export output | Directory (one file/trace) | Single JSONL file |
| When to use | Start here — gives full context | Drill into specific run types |

## Common Flags

### Data inclusion (use on `list` and `get`)

| Flag | Effect |
|------|--------|
| `--include-io` | Add inputs, outputs, error fields |
| `--include-metadata` | Add status, duration_ms, token_usage, costs, tags |
| `--include-feedback` | Add feedback_stats |
| `--full` | All three above combined (prefer `--include-io` on `run get`) |

### Filtering

| Flag | Description |
|------|-------------|
| `--project NAME` | Project name (or set `LANGSMITH_PROJECT` env var) |
| `--limit N` | Max results |
| `--last-n-minutes N` | Time window |
| `--since TIMESTAMP` | After this ISO timestamp |
| `--error` / `--no-error` | Filter by error status |
| `--name NAME` | Filter by run name (exact match) |
| `--min-latency SECONDS` | Minimum latency |
| `--max-latency SECONDS` | Maximum latency |
| `--min-tokens N` | Minimum total tokens |
| `--tags tag1,tag2` | Has any of these tags (OR) |
| `--trace-ids id1,id2` | Filter to specific traces |
| `--run-type TYPE` | `run list` only: llm, chain, tool, retriever, prompt, parser |
| `--filter QUERY` | Raw LangSmith filter DSL for complex cases |

**Display:**
- `--show-hierarchy` - (`trace list` only) Fetch full run tree inline for each trace

### Output

| Flag | Description |
|------|-------------|
| `--format json` | Machine-readable (default) |
| `--format pretty` | Human-readable tables, trees, syntax-highlighted JSON |
| `-o FILE` | Write output to file |

## Examples

```bash
# List projects and find recent activity
langsmith project list

# Recent traces with timing info
langsmith trace list --project default --limit 10 --include-metadata

# Failed traces in the last hour
langsmith trace list --project default --error --last-n-minutes 60

# Slow traces (>5s)
langsmith trace list --project default --min-latency 5.0 --limit 10

# Get full trace tree
langsmith trace get <trace-id> --project default

# All runs in a trace with IO (recommended for debugging)
langsmith run list --trace-ids <trace-id> --project default --include-io

# Only LLM runs (see model calls)
langsmith run list --trace-ids <trace-id> --project default --run-type llm --include-io

# Only tool runs (see tool inputs/outputs)
langsmith run list --trace-ids <trace-id> --project default --run-type tool --include-io

# Single run details
langsmith run get <run-id> --include-io

# Export traces for dataset creation
langsmith trace export ./traces --project default --limit 20 --full

# Advanced: filter by feedback score
langsmith trace list --filter 'and(eq(feedback_key, "correctness"), gte(feedback_score, 0.8))'
```

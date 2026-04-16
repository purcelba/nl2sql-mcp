# NL2SQL Confidence MCP Server

## Project Overview
An MCP server that exposes NL2SQL confidence scoring as tools usable inside Claude
Code and Cursor. Users ask natural language questions; the server scores confidence
across four dimensions and returns one of `proceed`, `clarify` (with rephrase
suggestions), or `reject` — gating SQL generation so bad questions never turn into
bad queries.

## Current Phase
**Phase 7 — Local Postgres for End-to-End Testing**
Phases 1–6 complete. See @docs/phases.md for full plan and progress tracking.

## MCP Tools
- `echo_confidence(question)` — plumbing smoke test (returns a fixed mock)
- `score_question(question)` — full four-dimension confidence breakdown
- `should_execute(question)` — gate pattern: returns a recommendation of
  `proceed`, `clarify`, or `reject`. On `clarify`, also returns a `suggestions`
  list of concrete rephrased questions. **Always call this before generating SQL.**

## Scoring Dimensions and Weights
Overall confidence is a weighted average:
- `semantic_match` (0.35) — tokenized question ∩ semantic-layer vocabulary
  (metrics, dimensions, entities). Uses a synonym map (customer→user, etc.)
- `llm_judge` (0.30) — Haiku rates answerability given the semantic layer
- `benchmark_proximity` (0.20) — cosine similarity to known-good benchmark
  questions (`semantic/benchmarks.yml`), `all-MiniLM-L6-v2` embeddings
- `sql_complexity` (0.15) — Haiku generates SQL, scorer counts joins /
  subqueries / window functions / CTEs / group bys

Gate thresholds (`src/mcp_server/gate.py`):
- `PROCEED_THRESHOLD = 0.65`
- `REJECT_THRESHOLD = 0.30`
- Hard-reject: any `semantic_match == 0.0` → `reject` regardless of overall

## Architecture Decisions
- Single MCP server; semantic layer + confidence scoring co-located
- stdio transport (Phase 6 decision — each developer runs their own instance)
- LLM calls use `claude-haiku-4-5-20251001` for speed/cost
- Rephrase suggestions fire only on the `clarify` branch to avoid wasted API calls
- Scorer functions accept an injectable `client` to keep them testable without
  hitting the real API

## Tech Stack
- Python 3.11+ (project uses 3.13 in `.venv`)
- `fastmcp` — tool registration + stdio transport
- `anthropic` — Haiku calls for sql_complexity, llm_judge, rephrase
- `sentence-transformers` — benchmark_proximity embeddings
- `pyyaml` — semantic layer + benchmarks + eval set
- Postgres in docker-compose (Phase 7) — real data for end-to-end testing
- No SQL execution from the MCP server itself

## Project Structure
```
nl2sql-mcp/
├── CLAUDE.md
├── docker-compose.yml              ← Phase 7
├── db/                             ← Phase 7: schema, seed, README
├── docs/
│   ├── phases.md                   ← progress tracker
│   ├── eval_baseline.md
│   ├── eval_tuned.md
│   └── failure_modes.md
├── scripts/
│   ├── run_eval.py                 ← label-matched eval harness
│   ├── inspect_failures.py
│   └── run_sql.py                  ← Phase 7
├── semantic/
│   ├── saas_metrics.yml            ← dummy MetricFlow semantic layer
│   ├── benchmarks.yml              ← known-good questions for proximity
│   └── eval_questions.yml          ← labeled evaluation set
├── src/
│   └── mcp_server/
│       ├── __init__.py
│       ├── server.py               ← tool registrations + wiring
│       ├── gate.py                 ← threshold logic for should_execute
│       ├── semantic_loader.py      ← YAML → dict helpers
│       └── scorers/
│           ├── semantic_match.py
│           ├── sql_complexity.py
│           ├── llm_judge.py
│           ├── benchmark_proximity.py
│           └── rephrase.py
└── tests/                          ← 41 tests, fixture-based for LLM scorers
```

## Conventions
- Tool names: snake_case verbs
- Every `@mcp.tool` needs a docstring — FastMCP exposes it as the tool description
  the calling LLM sees
- Tools return a dict with at least `confidence` (float 0–1) and `reasons` (list)
- LLM-backed scorers accept `client: Anthropic | None = None` for test injection
- Tests that would hit the real API must monkeypatch the relevant scorer or pass
  a fake client
- Never execute SQL from inside the MCP server; gate only
- Always convert relative dates to absolute dates when writing them into docs

## Key Commands
```bash
# Activate the venv
source .venv/bin/activate

# Install deps (if starting fresh)
.venv/bin/python -m pip install fastmcp anthropic sentence-transformers pyyaml pytest

# Run server manually to check for errors (stdio — ctrl-C to exit)
.venv/bin/python src/mcp_server/server.py

# Run tests
.venv/bin/python -m pytest tests/ -q

# Run the labeled eval and print a confusion matrix
.venv/bin/python scripts/run_eval.py

# Validate tools are visible in MCP Inspector (absolute paths required)
npx @modelcontextprotocol/inspector \
  /Users/bpurcell/Documents/Claude/Projects/nl2sql-mcp/.venv/bin/python \
  /Users/bpurcell/Documents/Claude/Projects/nl2sql-mcp/src/mcp_server/server.py
```

## Claude Code Config
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "nl2sql-confidence": {
      "command": "/absolute/path/to/nl2sql-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/nl2sql-mcp/src/mcp_server/server.py"],
      "cwd": "/absolute/path/to/nl2sql-mcp"
    }
  }
}
```
Use absolute paths — `python` alone may not resolve to the venv.

## Claude Code Workflow Tips
- After server code changes, `/mcp` reconnects so the new tools/behavior are live
- `/clear` between distinct phases keeps context clean
- Ask Claude Code to check off tasks in @docs/phases.md as you complete them

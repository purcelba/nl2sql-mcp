# Project Phases

## Phase 1 — Learn MCP Fundamentals ✓ DONE
**Goal:** Get a working MCP server with mock tools connected to Claude Code via stdio.
No real scoring logic. Prove the plumbing works end to end.

### Tasks
- [ ] Create project folder structure
- [ ] Install fastmcp: `pip install fastmcp`
- [ ] Write `src/mcp_server/server.py` with two mock tools:
  - `echo_confidence(question: str)` — returns a hardcoded mock score for any input
  - `score_question(question: str)` — returns a mock dict with all four scoring dimensions:
    semantic_match, sql_complexity, llm_judge, benchmark_proximity
- [ ] Verify server runs without errors: `python src/mcp_server/server.py`
- [ ] Write basic tests in `tests/test_server.py` that call each tool directly
- [ ] Register server in claude_desktop_config.json (see CLAUDE.md for snippet)
- [ ] Open Claude Code, confirm both tools appear, call them manually in chat
- [ ] Validate with MCP Inspector: `npx @modelcontextprotocol/inspector python src/mcp_server/server.py`

### What "done" looks like
You type "score this question: how many users signed up last week" in Claude Code
and get back a structured mock response with a confidence score and reasons list.

### Key things you will learn
- How FastMCP turns a Python function into an MCP tool
- How stdio transport works (Claude Code spawns your server as a subprocess)
- How Claude Code discovers and calls tools
- The edit loop: change server.py → restart → re-test

---

## Phase 2 — Real Scoring Logic ✓ DONE
**Goal:** Replace mock returns with real scoring logic backed by a dummy MetricFlow
semantic layer for a SaaS domain (users, events, subscriptions).

### Data model
The dummy semantic layer lives in `semantic/saas_metrics.yml` — a valid dbt MetricFlow
YAML file. No dbt Cloud needed; we just read and parse it as a Python dict.
The server loads it at startup and all scorers read from it.

### Tasks

**2a — Dummy semantic layer**
- [x] Create `semantic/saas_metrics.yml` with a realistic MetricFlow structure covering:
  - Semantic models: users, events, subscriptions
  - Entities: user_id, subscription_id, event_id
  - Dimensions: plan_type, event_type, signup_date, country
  - Measures: count of users, sum of mrr, count of events
  - Metrics: monthly_active_users, churn_rate, mrr, trial_conversion_rate,
    average_revenue_per_user
- [x] Write `src/mcp_server/semantic_loader.py` that parses the YAML into a Python dict
  at startup and exposes helper functions: `get_all_metrics()`, `get_all_dimensions()`,
  `get_all_entities()`
- [x] Write tests in `tests/test_semantic_loader.py` verifying the loader parses correctly

**2b — Semantic match scorer**
- [x] Replace mock `score_question` semantic_match dimension with real logic:
  - Tokenize the question
  - Compare against metric names, dimension names, and entity names from the semantic layer
  - Return a 0–1 score based on how many recognizable terms are found
  - Add matched and unmatched terms to the reasons list
- [x] Write tests covering: good match, partial match, no match

**2c — SQL complexity scorer**
- [x] Implement sql_complexity scoring:
  - Use the Anthropic API to generate the SQL the question would produce
  - Score based on: number of joins, presence of window functions, subqueries, group bys
  - Simple SELECT = high confidence (low complexity); many joins + window functions =
    lower confidence
  - Use `claude-haiku-4-5-20251001` for this — fast and cheap for a single generation
- [x] Write tests with a range of question complexities

**2d — LLM-as-judge scorer**
- [x] Implement llm_judge scoring:
  - Prompt the Anthropic API with the question + the semantic layer context
  - Ask it to rate answerability on a 0–1 scale with reasons
  - Parse the structured response back into confidence + reasons
  - Use `claude-haiku-4-5-20251001` for cost efficiency
- [x] Write tests mocking the API response

**2e — Benchmark proximity scorer**
- [x] Create `semantic/benchmarks.yml` with 15–20 known-good questions for the SaaS domain
  (e.g. "how many users signed up last month", "what is the MRR this quarter")
- [x] Implement benchmark_proximity scoring using sentence similarity:
  - Install `sentence-transformers` library
  - Embed the input question and all benchmark questions
  - Return cosine similarity to the nearest benchmark as the score
- [x] Write tests verifying similar questions score higher than dissimilar ones

**2f — Wire everything together**
- [x] Update `score_question()` to call all four real scorers and aggregate results
- [x] Add an overall confidence score: weighted average of the four dimensions
  (suggested starting weights: semantic_match 0.35, llm_judge 0.30,
  benchmark_proximity 0.20, sql_complexity 0.15)
- [x] Run the full test suite and verify end to end

### What "done" looks like
You ask "what is the monthly active users trend by plan type" and get back a structured
response with real per-dimension scores and specific reasons explaining each one.

---

## Phase 3 — Gate Pattern Tool ✓ DONE
**Goal:** Add the user-facing tool that makes the UX automatic. Claude Code calls
this first; the user never has to ask for a confidence check manually.

### Design
`should_execute(question)` → `{confidence, recommendation, dimensions, reasons, next_step}`
where `recommendation` is one of `proceed`, `clarify`, or `reject`.

### Tasks

**3a — Threshold configuration**
- [x] Define thresholds as module-level constants in `src/mcp_server/gate.py`:
  - `PROCEED_THRESHOLD = 0.75` (confidence ≥ this → proceed)
  - `REJECT_THRESHOLD = 0.40` (confidence < this → reject)
  - Between the two → clarify
- [x] Add a hard-reject rule: if `semantic_match == 0.0`, force reject regardless of
  overall score (prevents false-proceed when SQL complexity inflates confidence for
  out-of-scope questions — see Phase 2 testing observation)

**3b — Decision logic**
- [x] Write `src/mcp_server/gate.py` with `decide(dimensions, confidence) -> dict`:
  - Returns `{recommendation, next_step}` where `next_step` is a short
    action-oriented string (e.g. "generate SQL", "ask user to clarify event_type",
    "explain no matching semantic model")
  - For `clarify`, pick the lowest-scoring dimension and surface it as the reason
    the user needs to clarify
- [x] Unit tests for each branch: proceed, clarify, reject, hard-reject on zero
  semantic match

**3c — Expose `should_execute` MCP tool**
- [x] Add `should_execute(question)` tool in `server.py` that:
  - Calls the same four scorers as `score_question`
  - Passes dimensions + confidence through `decide()`
  - Returns the merged dict with `recommendation` and `next_step` on top
- [x] Docstring must be clear enough that Claude Code calls it *before* generating
  SQL (this is the whole point of the gate pattern)
- [x] Integration test calling `should_execute` directly with a good/ambiguous/bad
  question (uses monkeypatched scorers — `tests/test_should_execute.py`)

**3d — End-to-end verification in Claude Code**
- [x] Restart MCP server, reconnect
- [x] Call `should_execute` on three questions covering each branch and confirm
  the recommendation matches intuition
- [x] Note any mis-classifications for Phase 4 tuning
  - Observation: vague on-topic questions ("show me something interesting about our customers") hard-reject because vocabulary doesn't include synonyms (customer→user). Consider synonym expansion or softer semantic_match floor in Phase 4.

---

## Phase 4 — Integration Testing ✓ DONE
**Goal:** Stress-test the gate on a realistic question set, tune thresholds and
heuristics from the data, and document the failure modes that remain.

### Tasks

**4a — Labeled evaluation set**
- [x] Create `semantic/eval_questions.yml` with ~30 questions, each tagged with an
  expected label: `proceed`, `clarify`, or `reject`. Cover:
  - 10 clear/on-topic (expect proceed)
  - 10 ambiguous or partially mapped (expect clarify — e.g. "customer" instead of
    "user", missing time range, vague metric)
  - 10 out-of-scope or nonsensical (expect reject)
- [x] Include edge cases the Phase 3 manual testing surfaced (vague on-topic
  questions, synonyms like customer→user)

**4b — Eval harness**
- [x] Write `scripts/run_eval.py` that loads `eval_questions.yml`, calls
  `should_execute` on each, and prints a confusion matrix (expected vs actual
  recommendation) plus a per-question breakdown
- [x] Run it once against the current thresholds; save raw output to
  `docs/eval_baseline.md` so later tuning can be compared

**4c — Tune thresholds and heuristics**
- [x] From the baseline, identify mis-classifications:
  - Proceed cases that were clarify/reject → thresholds too strict or scorers
    undervaluing them
  - Reject cases that were proceed/clarify → thresholds too loose or
    sql_complexity inflating confidence
- [x] Adjust `PROCEED_THRESHOLD` / `REJECT_THRESHOLD` in `gate.py`, and/or adjust
  `WEIGHTS` in `server.py`
- [x] Consider adding a synonym map for common customer/user/buyer-type terms to
  feed into `semantic_match`
- [x] Re-run eval; commit the before/after confusion matrix to
  `docs/eval_tuned.md`

**4d — Document failure modes**
- [x] Create `docs/failure_modes.md` listing each remaining mis-classification
  with: question, expected, actual, per-dimension scores, and a hypothesis for
  why it fails
- [x] For each failure mode, note whether it's fixable in Phase 4 scope or should
  be escalated (e.g. needs a better embedding model, needs real dbt metadata,
  needs a fine-tuned judge)

**4e — Regression test**
- [x] Add `tests/test_eval_regression.py` that runs a small subset (3-5
  questions) of the eval set through `should_execute` (with monkeypatched
  scorers or cached fixtures to avoid API calls) and asserts the recommendations
  match the labels — guards against future tuning regressions

---

## Phase 5 — Rephrase Suggestions for Ambiguous Questions ✓ DONE
**Goal:** When the gate returns `clarify`, also return concrete, actionable
rephrasing suggestions grounded in the semantic layer. Turn "this is ambiguous"
into "did you mean one of these?"

### Design
Extend the `clarify` branch so `next_step` is joined by a `suggestions` list
(2-4 concrete rephrased questions the user could pick from). `proceed` and
`reject` branches unchanged.

### Tasks

**5a — Rephrase generator**
- [x] Write `src/mcp_server/scorers/rephrase.py` with
  `suggest_rephrases(question, dimensions) -> list[str]` that calls Haiku
  with:
  - the user's question
  - the full list of metrics, dimensions, entities from the semantic layer
  - the nearest benchmark question (already computed in `benchmark_proximity`)
  - the matched/unmatched terms from `semantic_match`
  - instructions to return 2-4 specific, well-formed alternative questions
    that map onto available metrics/dimensions
- [x] Return a parsed `list[str]`; on parse failure, return `[]` (suggestions
  are best-effort, never block the recommendation)

**5b — Wire into the gate**
- [x] In `server.py` `should_execute`, only call `suggest_rephrases` when
  `recommendation == "clarify"` (skip the cost on proceed/reject)
- [x] Add `suggestions` to the returned dict; update the tool docstring so
  Claude Code knows to surface them to the user verbatim

**5c — Tests**
- [x] Unit test `suggest_rephrases` with an injected fake Anthropic client,
  verifying parsing of good output, graceful handling of malformed output,
  and that the prompt includes semantic-layer context
- [x] Integration test for `should_execute` that monkeypatches scorers to
  force the clarify branch and asserts `suggestions` is populated

**5d — Manual verification**
- [x] Reconnect MCP server, call `should_execute` on 3 known-ambiguous
  questions from the eval set and confirm the suggestions are useful
- [x] Note any bad suggestions in `docs/failure_modes.md`

---

## Phase 6 — Transport Decision ✓ DONE
**Decision:** keep **stdio**. Each developer runs their own local instance;
no need to share a hosted server. Revisit if a team deployment becomes needed.

---

## Phase 7 — Local Postgres for End-to-End Testing ✓ DONE
**Goal:** Stand up a real Postgres warehouse locally via docker-compose,
populated with data matching the semantic layer, so we can execute the SQL
that `should_execute` greenlights and validate results end-to-end.

### Design
- `docker-compose.yml` at the repo root runs Postgres on a fixed port
- Schema + seed data live in `db/` (init scripts auto-loaded by the Postgres
  container on first boot)
- Schema mirrors the dbt model refs used in the semantic layer: `dim_users`,
  `fct_events`, `fct_subscriptions`
- Keep it small: ~500 users, ~5k events, ~800 subscriptions — enough to get
  non-trivial answers without slow seeding
- Do NOT add SQL execution to the MCP server yet (still a separate concern).
  A standalone `scripts/run_sql.py` is enough for manual testing.

### Tasks

**7a — docker-compose + schema**
- [x] Add `docker-compose.yml` with a single `postgres:16` service, named
  volume for persistence, env vars for user/password/db, port 5432 mapped
- [x] Create `db/01_schema.sql` defining `dim_users`, `fct_events`,
  `fct_subscriptions` with columns matching the dimensions/measures in
  `semantic/saas_metrics.yml` (plus primary keys and foreign keys on
  `user_id`)
- [x] Document `docker compose up -d` / `down` usage in a short
  `db/README.md`

**7b — Seed data**
- [x] Write `db/02_seed.sql` (or `db/seed.py` if generation logic is
  non-trivial) that inserts ~500 users spread across signup_date, plan_type,
  country; ~800 subscriptions (mix of trial/paid, some churned); ~5k events
  across the user base in the last 90 days
- [x] Verify with `docker compose exec postgres psql ... -c "SELECT ..."`
  that row counts and distributions look reasonable

**7c — SQL runner**
- [x] Add `scripts/run_sql.py` that connects to local Postgres (env vars or
  defaults), takes a SQL string on stdin or via arg, and prints results as a
  nicely formatted table
- [x] Add `psycopg[binary]` to the installed deps
- [x] Manual smoke test: run the example query from the "new users in
  january" rephrase and confirm it returns expected results

**7d — End-to-end walkthrough**
- [x] Pick 3 eval-set proceed questions. For each:
  1. Call `should_execute` via MCP — confirm `proceed`
  2. Generate SQL with Haiku (reuse `_generate_sql` from sql_complexity
     scorer via a small wrapper if convenient)
  3. Run the SQL through `scripts/run_sql.py`
  4. Sanity-check results
- [x] Document the walkthrough in `docs/e2e_walkthrough.md`

**7e — CI-safe tests**
- [x] Mark any tests that actually connect to Postgres with a pytest marker
  (e.g. `@pytest.mark.db`) and skip by default — tests should still pass
  without the container running
- [x] Add a short "running the db-backed tests" section to `db/README.md`

# End-to-end walkthrough

Runs three eval-set `proceed` questions through the full pipeline:
**gate (`should_execute`) → SQL generation (Haiku) → execute (Postgres) → sanity-check**.

Reproduce with `scripts/e2e_walkthrough.py` after `docker compose up -d` and
`python db/seed.py`. Run on 2026-04-16 with the deterministic seed.

## 1. "what is the mrr this quarter"

- **Gate:** proceed, confidence 0.82
- **Generated SQL:**
  ```sql
  SELECT SUM(monthly_recurring_revenue) as mrr
  FROM fct_subscriptions
  WHERE ended_at IS NULL
    AND started_at <= CURRENT_DATE
    AND EXTRACT(QUARTER FROM CURRENT_DATE) = EXTRACT(QUARTER FROM started_at)
    AND EXTRACT(YEAR FROM CURRENT_DATE) = EXTRACT(YEAR FROM started_at);
  ```
- **Result:** `mrr = 1457.00`
- **Sanity check:** **questionable.** Real active MRR across all subscriptions
  is $25,324. Haiku interpreted "mrr this quarter" as "MRR from subscriptions
  *started* this quarter", which is a plausible reading but usually isn't what
  a stakeholder means. The gate said proceed because the question maps cleanly
  to available metrics — but gate confidence does not measure SQL semantic
  correctness. This is a new failure mode worth noting.

## 2. "count of subscriptions by plan type"

- **Gate:** proceed, confidence 0.82
- **Generated SQL:**
  ```sql
  SELECT plan_type, COUNT(*) as subscription_count
  FROM fct_subscriptions
  GROUP BY plan_type
  ORDER BY subscription_count DESC;
  ```
- **Result:** `free=346, pro=345, enterprise=109`
- **Sanity check:** ✓ 346 + 345 + 109 = 800, matches the seed.

## 3. "how many events happened yesterday by event type"

- **Gate:** proceed, confidence 0.76
- **Generated SQL:**
  ```sql
  SELECT event_type, COUNT(*) as event_count
  FROM fct_events
  WHERE DATE(event_timestamp) = CURRENT_DATE - INTERVAL '1 day'
  GROUP BY event_type
  ORDER BY event_count DESC;
  ```
- **Result (2026-04-15):** `invite_user=16, export_csv=14, view_dashboard=12,
  login=11, run_query=7` — total 60 events
- **Sanity check:** ✓ ~55/day average across 5000 events / 90 days; 60 sits in
  the expected range.

## New failure mode surfaced

Gate confidence scores *question-to-semantic-layer alignment* but **not**
*SQL semantic correctness*. Q1 demonstrates this: the question mapped
unambiguously to a known metric, so confidence was 0.82, but the generated
SQL gave a misleading answer because Haiku's interpretation of "this quarter"
differed from the likely user intent.

Possible mitigations (future phase, not in 7):
- Add a post-generation review step where Haiku is shown the SQL it just wrote
  and asked whether it actually answers the original question
- Display the generated SQL to the user for approval before execution
- For MRR specifically, clarify prompt wording: "MRR from *all active*
  subscriptions" vs. "MRR from subscriptions that started this quarter"

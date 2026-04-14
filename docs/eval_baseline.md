# Gate evaluation — baseline (pre-tuning)

Ran `scripts/run_eval.py` against `semantic/eval_questions.yml` on 2026-04-14
with the initial Phase 3 thresholds (`PROCEED ≥ 0.75`, `REJECT < 0.40`, hard-reject
on `semantic_match == 0`) and weights
(semantic_match=0.35, llm_judge=0.30, benchmark_proximity=0.20, sql_complexity=0.15).

## Confusion matrix

|   expected \ actual |  proceed |  clarify |   reject |
|---------------------|---------:|---------:|---------:|
|             proceed |        7 |        3 |        0 |
|             clarify |        2 |        1 |        7 |
|              reject |        0 |        0 |       10 |

**Accuracy: 18/30 = 60.0%**

## Per-question results

| expected | actual | conf | question |
|---|---|---:|---|
| proceed | proceed | 0.80 | what is the mrr this quarter |
| proceed | clarify | 0.69 | how many users signed up last month |
| proceed | proceed | 0.93 | show monthly active users trend by plan type |
| proceed | proceed | 0.78 | what is the churn rate for the pro plan last quarter |
| proceed | proceed | 0.91 | average revenue per user by country this year |
| proceed | proceed | 0.82 | count of subscriptions by plan type |
| proceed | proceed | 0.76 | how many events happened yesterday by event type |
| proceed | proceed | 0.87 | trial conversion rate by plan type for the last 6 months |
| proceed | clarify | 0.66 | mrr growth rate month over month |
| proceed | clarify | 0.67 | how many users had at least one event last week |
| clarify | reject  | 0.45 | show me customer growth |
| clarify | proceed | 0.92 | what is our revenue |
| clarify | reject  | 0.22 | how are things going this month |
| clarify | reject  | 0.37 | compare plans |
| clarify | clarify | 0.50 | user activity last week |
| clarify | reject  | 0.37 | top customers by spend |
| clarify | proceed | 0.92 | churn |
| clarify | reject  | 0.40 | signups |
| clarify | reject  | 0.40 | enterprise breakdown |
| clarify | reject  | 0.22 | what changed recently |
| reject  | reject  | 0.20 | what is the weather in tokyo today |
| reject  | reject  | 0.20 | how many widgets did we ship |
| reject  | reject  | 0.22 | list all employee salaries |
| reject  | reject  | 0.18 | what is the capital of france |
| reject  | reject  | 0.18 | show me the source code of this server |
| reject  | reject  | 0.20 | who is the ceo |
| reject  | reject  | 0.17 | translate this question to spanish |
| reject  | reject  | 0.31 | generate a marketing email for our pro plan |
| reject  | reject  | 0.19 | what stock should i buy today |
| reject  | reject  | 0.19 | asdf qwerty zxcv |

## Observations

1. **Reject is perfect (10/10)** — the hard-reject on `semantic_match == 0` is
   doing heavy lifting.
2. **Clarify is the weakest class (1/10)**. Two distinct failure modes:
   - Synonym blindness: "customer", "spend", "revenue" are rejected because they
     don't appear in the vocabulary (customer→user, spend→mrr, revenue→mrr).
   - Thresholds too aggressive: genuine clarify-band scores (0.37–0.45) fall
     below the 0.40 reject line.
3. **Proceed near-misses**: three clear questions landed at 0.66–0.69, just
   under the 0.75 proceed line. Lowering `PROCEED_THRESHOLD` a touch (or
   raising sql_complexity / benchmark_proximity weight) would catch them.
4. **Interesting mis-proceeds**: "what is our revenue" (0.92) and "churn"
   (0.92) — high overall confidence masks that they lack a time window or
   qualifier. These should be clarify, not proceed. Current scoring can't
   detect missing qualifiers.

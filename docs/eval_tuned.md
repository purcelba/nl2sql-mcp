# Gate evaluation — after Phase 4c tuning

## Changes from baseline
- Lowered `PROCEED_THRESHOLD` 0.75 → **0.65**
- Lowered `REJECT_THRESHOLD` 0.40 → **0.30**
- Added `SYNONYMS` map in `semantic_match.py` (customer→user, revenue→mrr,
  spend→mrr, plans→plan, signup(s)→signup_date, growth→trend, etc.)
- Weights unchanged

## Confusion matrix (tuned)

|   expected \ actual |  proceed |  clarify |   reject |
|---------------------|---------:|---------:|---------:|
|             proceed |        9 |        1 |        0 |
|             clarify |        3 |        4 |        3 |
|              reject |        0 |        1 |        9 |

**Accuracy: 22/30 = 73.3%** (baseline was 18/30 = 60.0%)

### Per-class delta
- proceed: 7 → 9 (+2)
- clarify: 1 → 4 (+3)
- reject:  10 → 9 (−1, one false-clarify)

## Remaining mis-classifications

| expected | actual | conf | question | notes |
|---|---|---:|---|---|
| proceed | clarify | 0.64 | how many users signed up last month | just under the 0.65 line |
| clarify | proceed | 0.92 | what is our revenue | missing time window; scorers don't detect missing qualifiers |
| clarify | proceed | 0.93 | churn | bare metric word with full benchmark+judge support |
| clarify | proceed | 0.75 | signups | synonym map matched signup_date; no qualifier required |
| clarify | reject  | 0.22 | how are things going this month | almost nothing semantic |
| clarify | reject  | 0.39 | enterprise breakdown | "enterprise" unmatched; only "breakdown" is stopword-ish |
| clarify | reject  | 0.21 | what changed recently | arguably should stay reject — label may be generous |
| reject  | clarify | 0.31 | generate a marketing email for our pro plan | "pro plan" matched, action verb ignored |

## Observations for Phase 5+
- **Missing-qualifier detection** is the biggest remaining gap. Bare metric
  words ("churn", "signups", "revenue") score high overall but lack time range
  or grouping. This is exactly what rephrase suggestions (Phase 5) should
  address.
- **Intent-vs-analytics** confusion: "generate a marketing email" is an action
  request, not an analytics question. A separate intent classifier (or a
  stricter judge prompt) would catch this.
- **Label ambiguity**: "what changed recently" and "how are things going this
  month" are arguably better as reject than clarify. Eval labels are a
  judgment call.

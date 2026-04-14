# Failure modes — post-Phase 4c

Mis-classifications remaining after threshold + synonym tuning. Per-dimension
scores captured via `scripts/inspect_failures.py` on 2026-04-14.

> LLM scorers (`sql_complexity`, `llm_judge`) are non-deterministic. Scores vary
> run-to-run by ±0.05-0.1. "how many users signed up last month" which clarified
> at 0.64 in one run proceeded at 0.76 in the next — the class boundary is
> genuinely fuzzy here, not broken.

## 1. Bare-metric questions proceed without a qualifier

| question | expected | actual | conf | sm | sc | lj | bp |
|---|---|---|---:|---:|---:|---:|---:|
| what is our revenue | clarify | proceed | 0.89 | 1.00 | 1.00 | 0.90 | 0.59 |
| churn | clarify | proceed | 0.93 | 1.00 | 0.95 | 1.00 | 0.70 |
| signups | clarify | proceed | 0.75 | 1.00 | 0.95 | 0.50 | 0.54 |

**Root cause:** scorers reward that the metric exists, but none of them check
whether the question specifies a time window, grouping, or filter. Haiku's
judge even rates "churn" 1.0 because *churn the metric* is indeed answerable.

**Fixability in this phase:** no. This requires a separate "qualifier
completeness" check.

**Escalate to:** Phase 5 rephrase suggestions — turn "churn" into
"did you mean churn rate last month? churn rate by plan?" The ambiguity
becomes the feature.

## 2. Out-of-scope verbs masquerade as analytics

| question | expected | actual | conf | sm | sc | lj | bp |
|---|---|---|---:|---:|---:|---:|---:|
| generate a marketing email for our pro plan | reject | clarify | 0.31 | 0.20 | 1.00 | 0.00 | 0.47 |

**Root cause:** semantic_match sees `pro`, `plan` and scores non-zero,
bypassing the `sm == 0` hard-reject. Benchmark_proximity also gives partial
credit via "pro" overlap.

**Fixability in this phase:** partial. Could raise the hard-reject threshold
from exact `0.0` to `< 0.15`, but that would regress some legitimate clarify
cases. Better: an intent classifier (is this an analytics question?) as a
pre-filter.

**Escalate to:** future phase or tightened judge prompt that explicitly rejects
non-question actions ("generate", "email", "translate", "summarize").

## 3. Ambiguous on-topic phrases with no concrete terms

| question | expected | actual | conf | sm | sc | lj | bp |
|---|---|---|---:|---:|---:|---:|---:|
| how are things going this month | clarify | reject | 0.21 | 0.00 | 0.85 | 0.00 | 0.39 |
| what changed recently | clarify | reject | 0.21 | 0.00 | 0.95 | 0.00 | 0.35 |

**Root cause:** zero semantic match triggers the hard-reject. Benchmark
proximity is low (~0.35-0.39) because the phrasing is generic.

**Fixability in this phase:** no — the labels are arguably wrong. These
questions genuinely contain zero analytic content. Phase 4 label review would
likely re-tag them as `reject`.

**Escalate to:** label review in a follow-up, not a code change.

## 4. Under-covered dimension value

| question | expected | actual | conf | sm | sc | lj | bp |
|---|---|---|---:|---:|---:|---:|---:|
| enterprise breakdown | clarify | reject | 0.39 | 0.00 | 0.85 | 0.50 | 0.55 |

**Root cause:** "enterprise" is a plausible value of `plan_type` but not a
dimension/metric name itself, so semantic_match gives it zero and hard-rejects.
The judge gives 0.5 (partial answerability). Confidence 0.39 is just above the
0.30 reject threshold, so without the hard-reject, this would have clarified.

**Fixability in this phase:** yes, but not cheaply. We'd need dimension *value*
matching (enumerated values like plan_type = {free, pro, enterprise}) — either
from the semantic layer YAML or from a data-profile pass. Out of Phase 4 scope.

**Escalate to:** semantic-layer enrichment — add enumerated values to YAML.

## Summary

| failure mode | count | fixable now | escalation path |
|---|---:|---|---|
| bare metric without qualifier | 3 | no | Phase 5 rephrase |
| out-of-scope verb partially matches | 1 | partial | intent classifier / stricter judge |
| generic ambiguous phrasing | 2 | no | label review |
| dimension value unmatched | 1 | yes (costly) | semantic-layer enrichment |

Net effect: tuning has exhausted the easy wins. Remaining improvements need
architectural additions (Phase 5 suggestions, intent filter, enum values in
semantic layer), not parameter tweaks.

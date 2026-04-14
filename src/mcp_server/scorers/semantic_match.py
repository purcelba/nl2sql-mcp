"""Semantic match scorer: compare question tokens to semantic layer vocabulary."""

import re

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
)

STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "for", "to", "by", "with",
    "how", "many", "much", "what", "which", "who", "where", "when", "is",
    "are", "was", "were", "be", "been", "do", "does", "did", "have", "has",
    "and", "or", "but", "this", "that", "these", "those", "me", "my", "our",
    "us", "it", "its", "per", "show", "tell", "give", "get", "list",
}

# Map user-facing synonyms to canonical semantic-layer terms.
SYNONYMS = {
    "customer": "user",
    "customers": "user",
    "buyer": "user",
    "buyers": "user",
    "account": "user",
    "accounts": "user",
    "users": "user",
    "revenue": "mrr",
    "spend": "mrr",
    "arr": "mrr",
    "plans": "plan",
    "signup": "signup_date",
    "signups": "signup_date",
    "signed": "signup_date",
    "growth": "trend",
}


def _tokenize(text: str) -> set[str]:
    raw = re.findall(r"[a-z0-9]+", text.lower())
    tokens = {t for t in raw if t not in STOPWORDS and len(t) > 1}
    return {SYNONYMS.get(t, t) for t in tokens}


def _vocabulary() -> set[str]:
    vocab: set[str] = set()
    for name in get_all_metrics() + get_all_dimensions() + get_all_entities():
        vocab.add(name.lower())
        vocab.update(name.lower().split("_"))
    vocab.discard("id")
    return vocab


def score_semantic_match(question: str) -> dict:
    tokens = _tokenize(question)
    if not tokens:
        return {
            "score": 0.0,
            "matched": [],
            "unmatched": [],
            "reason": "no meaningful terms extracted from question",
        }
    vocab = _vocabulary()
    matched = sorted(tokens & vocab)
    unmatched = sorted(tokens - vocab)
    score = len(matched) / len(tokens)
    return {
        "score": score,
        "matched": matched,
        "unmatched": unmatched,
        "reason": (
            f"matched {len(matched)}/{len(tokens)} terms against semantic layer: "
            f"matched={matched} unmatched={unmatched}"
        ),
    }

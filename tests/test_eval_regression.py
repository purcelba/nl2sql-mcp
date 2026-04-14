"""Regression guard: a small, stable subset of the eval set with
fixed per-dimension scores so we can verify the gate's decision logic
without hitting real APIs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from mcp_server import server

# (question, expected recommendation, dimension fixture)
# Scores taken from representative runs in docs/eval_tuned.md.
CASES = [
    (
        "show monthly active users trend by plan type",
        "proceed",
        {"sm": 0.83, "sc": 0.95, "lj": 1.0, "bp": 0.85},
    ),
    (
        "average revenue per user by country this year",
        "proceed",
        {"sm": 0.83, "sc": 0.9, "lj": 1.0, "bp": 0.9},
    ),
    (
        "user activity last week",
        "clarify",
        {"sm": 0.33, "sc": 0.85, "lj": 0.5, "bp": 0.45},
    ),
    (
        "what is the weather in tokyo today",
        "reject",
        {"sm": 0.0, "sc": 0.95, "lj": 0.0, "bp": 0.08},
    ),
    (
        "what is the capital of france",
        "reject",
        {"sm": 0.0, "sc": 0.95, "lj": 0.0, "bp": 0.15},
    ),
]


@pytest.mark.parametrize("question,expected,dims", CASES)
def test_gate_recommendation_matches_label(monkeypatch, question, expected, dims):
    monkeypatch.setattr(
        server,
        "score_semantic_match",
        lambda q: {"score": dims["sm"], "reason": "fixture"},
    )
    monkeypatch.setattr(
        server,
        "score_sql_complexity",
        lambda q: {"score": dims["sc"], "reason": "fixture"},
    )
    monkeypatch.setattr(
        server,
        "score_llm_judge",
        lambda q: {"score": dims["lj"], "reason": "fixture"},
    )
    monkeypatch.setattr(
        server,
        "score_benchmark_proximity",
        lambda q: {"score": dims["bp"], "reason": "fixture"},
    )
    result = server.should_execute(question)
    assert result["recommendation"] == expected, (
        f"{question!r}: expected {expected}, got {result['recommendation']} "
        f"(confidence={result['confidence']:.2f})"
    )

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from mcp_server import server


@pytest.fixture
def fake_scorers(monkeypatch):
    def make(sm, sc, lj, bp):
        monkeypatch.setattr(
            server, "score_semantic_match", lambda q: {"score": sm, "reason": "fake"}
        )
        monkeypatch.setattr(
            server, "score_sql_complexity", lambda q: {"score": sc, "reason": "fake"}
        )
        monkeypatch.setattr(
            server, "score_llm_judge", lambda q: {"score": lj, "reason": "fake"}
        )
        monkeypatch.setattr(
            server,
            "score_benchmark_proximity",
            lambda q: {"score": bp, "reason": "fake"},
        )
    return make


def test_should_execute_good_question_proceeds(fake_scorers):
    fake_scorers(sm=0.9, sc=0.95, lj=1.0, bp=0.9)
    result = server.should_execute("good question")
    assert result["recommendation"] == "proceed"


def test_should_execute_ambiguous_question_clarifies(monkeypatch, fake_scorers):
    fake_scorers(sm=0.5, sc=0.7, lj=0.6, bp=0.5)
    monkeypatch.setattr(server, "suggest_rephrases", lambda *a, **kw: [])
    result = server.should_execute("ambiguous question")
    assert result["recommendation"] == "clarify"


def test_should_execute_out_of_scope_rejects(fake_scorers):
    fake_scorers(sm=0.0, sc=1.0, lj=0.0, bp=0.1)
    result = server.should_execute("out of scope")
    assert result["recommendation"] == "reject"

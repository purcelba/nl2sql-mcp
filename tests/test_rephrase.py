import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from mcp_server import server
from mcp_server.scorers.rephrase import _parse, suggest_rephrases


class FakeClient:
    def __init__(self, text: str, capture=None):
        self._text = text
        self._capture = capture
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        if self._capture is not None:
            self._capture.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text=self._text)])


def test_parse_valid_array():
    out = _parse('["a", "b", "c"]')
    assert out == ["a", "b", "c"]


def test_parse_wrapped_in_prose():
    out = _parse('Here are some ideas:\n["x", "y"]\nHope that helps.')
    assert out == ["x", "y"]


def test_parse_garbage_returns_empty():
    assert _parse("not json") == []


def test_parse_invalid_json_returns_empty():
    assert _parse('["missing', ) == []


def test_suggest_rephrases_injects_context():
    capture: list = []
    client = FakeClient('["what is mrr this month", "mrr by plan type"]', capture=capture)
    out = suggest_rephrases(
        "revenue",
        dimensions={"semantic_match": 0.5},
        nearest_benchmark="what is the mrr this quarter",
        matched_terms=["mrr"],
        unmatched_terms=["revenue"],
        client=client,
    )
    assert out == ["what is mrr this month", "mrr by plan type"]
    user_msg = capture[0]["messages"][0]["content"]
    assert "revenue" in user_msg
    assert "what is the mrr this quarter" in user_msg
    system = capture[0]["system"]
    assert "mrr" in system  # metric list present


def test_suggest_rephrases_malformed_returns_empty():
    client = FakeClient("sorry, can't help")
    out = suggest_rephrases("x", dimensions={}, client=client)
    assert out == []


@pytest.fixture
def fake_scorers(monkeypatch):
    def make(sm, sc, lj, bp):
        monkeypatch.setattr(
            server,
            "score_semantic_match",
            lambda q: {"score": sm, "reason": "f", "matched": ["mrr"], "unmatched": ["foo"]},
        )
        monkeypatch.setattr(
            server, "score_sql_complexity", lambda q: {"score": sc, "reason": "f"}
        )
        monkeypatch.setattr(
            server, "score_llm_judge", lambda q: {"score": lj, "reason": "f"}
        )
        monkeypatch.setattr(
            server,
            "score_benchmark_proximity",
            lambda q: {"score": bp, "reason": "f", "nearest": "benchmark"},
        )
    return make


def test_clarify_branch_populates_suggestions(monkeypatch, fake_scorers):
    fake_scorers(sm=0.5, sc=0.7, lj=0.5, bp=0.5)
    monkeypatch.setattr(
        server, "suggest_rephrases", lambda *a, **kw: ["rephrase A", "rephrase B"]
    )
    result = server.should_execute("ambiguous q")
    assert result["recommendation"] == "clarify"
    assert result["suggestions"] == ["rephrase A", "rephrase B"]


def test_proceed_branch_skips_suggestions(monkeypatch, fake_scorers):
    fake_scorers(sm=0.9, sc=0.95, lj=1.0, bp=0.9)
    calls: list = []
    monkeypatch.setattr(
        server,
        "suggest_rephrases",
        lambda *a, **kw: calls.append(1) or [],
    )
    result = server.should_execute("clear q")
    assert result["recommendation"] == "proceed"
    assert result["suggestions"] == []
    assert calls == []  # not called on proceed


def test_reject_branch_skips_suggestions(monkeypatch, fake_scorers):
    fake_scorers(sm=0.0, sc=1.0, lj=0.0, bp=0.1)
    calls: list = []
    monkeypatch.setattr(
        server,
        "suggest_rephrases",
        lambda *a, **kw: calls.append(1) or [],
    )
    result = server.should_execute("out of scope")
    assert result["recommendation"] == "reject"
    assert result["suggestions"] == []
    assert calls == []

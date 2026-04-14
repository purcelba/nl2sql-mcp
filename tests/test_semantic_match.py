import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.scorers.semantic_match import score_semantic_match


def test_good_match_scores_high():
    result = score_semantic_match("show mrr by plan type and country")
    assert result["score"] >= 0.6
    assert "mrr" in result["matched"]
    assert "plan" in result["matched"] or "plan_type" in result["matched"]


def test_no_match_scores_zero():
    result = score_semantic_match("what is the weather in tokyo today")
    assert result["score"] == 0.0
    assert result["matched"] == []


def test_partial_match_scores_between():
    result = score_semantic_match("churn rate for enterprise customers yesterday")
    assert 0.0 < result["score"] < 1.0
    assert "churn" in result["matched"]


def test_empty_question_scores_zero():
    result = score_semantic_match("the of")
    assert result["score"] == 0.0

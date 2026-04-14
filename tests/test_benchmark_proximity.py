import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.scorers.benchmark_proximity import score_benchmark_proximity


def test_similar_question_scores_higher_than_dissimilar():
    similar = score_benchmark_proximity("what's the mrr for this quarter")
    dissimilar = score_benchmark_proximity("what color is the sky today")
    assert similar["score"] > dissimilar["score"]
    assert similar["score"] > 0.5


def test_exact_benchmark_question_scores_near_one():
    result = score_benchmark_proximity("what is the mrr this quarter")
    assert result["score"] > 0.95


def test_returns_nearest_benchmark():
    result = score_benchmark_proximity("how many users signed up")
    assert "signed up" in result["nearest"]

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.gate import decide


def _dims(sm=0.8, sc=0.8, lj=0.8, bp=0.8):
    return {
        "semantic_match": sm,
        "sql_complexity": sc,
        "llm_judge": lj,
        "benchmark_proximity": bp,
    }


def test_proceed_when_confidence_high():
    result = decide(_dims(), confidence=0.85)
    assert result["recommendation"] == "proceed"
    assert "generate SQL" in result["next_step"]


def test_reject_when_confidence_low():
    result = decide(_dims(sm=0.2, lj=0.2, bp=0.2, sc=0.2), confidence=0.2)
    assert result["recommendation"] == "reject"


def test_clarify_in_middle_band():
    result = decide(_dims(sm=0.5, lj=0.6, bp=0.7, sc=0.5), confidence=0.55)
    assert result["recommendation"] == "clarify"
    assert "semantic_match" in result["next_step"] or "sql_complexity" in result["next_step"]


def test_hard_reject_on_zero_semantic_match():
    result = decide(_dims(sm=0.0, sc=1.0, lj=1.0, bp=1.0), confidence=0.80)
    assert result["recommendation"] == "reject"
    assert "no matching semantic model" in result["next_step"]

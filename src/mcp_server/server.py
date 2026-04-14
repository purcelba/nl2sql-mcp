"""NL2SQL Confidence MCP server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastmcp import FastMCP

from mcp_server.gate import decide
from mcp_server.scorers.benchmark_proximity import score_benchmark_proximity
from mcp_server.scorers.llm_judge import score_llm_judge
from mcp_server.scorers.rephrase import suggest_rephrases
from mcp_server.scorers.semantic_match import score_semantic_match
from mcp_server.scorers.sql_complexity import score_sql_complexity

WEIGHTS = {
    "semantic_match": 0.35,
    "llm_judge": 0.30,
    "benchmark_proximity": 0.20,
    "sql_complexity": 0.15,
}

mcp = FastMCP("nl2sql-confidence")


@mcp.tool
def echo_confidence(question: str) -> dict:
    """Return a hardcoded mock confidence score for any question.

    Use this to verify the MCP plumbing works end to end. The score is
    not derived from the question — it's a fixed placeholder.
    """
    return {
        "question": question,
        "confidence": 0.75,
        "reasons": ["mock score — echo_confidence always returns 0.75"],
    }


@mcp.tool
def score_question(question: str) -> dict:
    """Return a confidence breakdown across all four scoring dimensions.

    Dimensions:
    - semantic_match: how well the question maps to the semantic model
    - sql_complexity: estimated complexity of the resulting SQL
    - llm_judge: an LLM's rating of answerability
    - benchmark_proximity: similarity to known-good benchmark questions
    """
    sm = score_semantic_match(question)
    sc = score_sql_complexity(question)
    lj = score_llm_judge(question)
    bp = score_benchmark_proximity(question)
    dimensions = {
        "semantic_match": sm["score"],
        "sql_complexity": sc["score"],
        "llm_judge": lj["score"],
        "benchmark_proximity": bp["score"],
    }
    confidence = sum(dimensions[k] * WEIGHTS[k] for k in dimensions)
    return {
        "question": question,
        "confidence": confidence,
        "dimensions": dimensions,
        "weights": WEIGHTS,
        "reasons": [
            f"semantic_match: {sm['reason']}",
            f"sql_complexity: {sc['reason']}",
            lj["reason"],
            f"benchmark_proximity: {bp['reason']}",
        ],
        "_scorer_details": {
            "matched": sm.get("matched", []),
            "unmatched": sm.get("unmatched", []),
            "nearest_benchmark": bp.get("nearest"),
        },
    }


@mcp.tool
def should_execute(question: str) -> dict:
    """Decide whether to proceed with SQL generation for a natural-language question.

    ALWAYS call this before generating or executing SQL for a user's analytics
    question. It runs confidence scoring across four dimensions and returns a
    single recommendation: proceed, clarify, or reject.

    - proceed: confidence is high; generate and run SQL
    - clarify: confidence is middling; surface the `suggestions` list to the user
      verbatim and let them pick one before generating SQL
    - reject: confidence is too low or no semantic match; explain why, do not attempt SQL
    """
    result = score_question(question)
    decision = decide(result["dimensions"], result["confidence"])
    suggestions: list[str] = []
    if decision["recommendation"] == "clarify":
        details = result.get("_scorer_details", {})
        suggestions = suggest_rephrases(
            question,
            dimensions=result["dimensions"],
            nearest_benchmark=details.get("nearest_benchmark"),
            matched_terms=details.get("matched"),
            unmatched_terms=details.get("unmatched"),
        )
    result.pop("_scorer_details", None)
    return {**result, **decision, "suggestions": suggestions}


if __name__ == "__main__":
    mcp.run()

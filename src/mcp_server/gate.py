"""Gate pattern decision logic — translate scores into a recommendation."""

PROCEED_THRESHOLD = 0.65
REJECT_THRESHOLD = 0.30


def decide(dimensions: dict[str, float], confidence: float) -> dict:
    if dimensions.get("semantic_match", 0.0) == 0.0:
        return {
            "recommendation": "reject",
            "next_step": "explain no matching semantic model — question terms do not map to any metric, dimension, or entity",
        }

    if confidence >= PROCEED_THRESHOLD:
        return {
            "recommendation": "proceed",
            "next_step": "generate SQL",
        }

    if confidence < REJECT_THRESHOLD:
        return {
            "recommendation": "reject",
            "next_step": "explain low overall confidence and do not attempt SQL",
        }

    weakest = min(dimensions, key=dimensions.get)
    return {
        "recommendation": "clarify",
        "next_step": f"ask user to clarify — weakest dimension is {weakest} (score {dimensions[weakest]:.2f})",
    }

"""Print per-dimension scores for a hand-picked list of questions."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_server.server import should_execute  # noqa: E402

QUESTIONS = [
    "how many users signed up last month",
    "what is our revenue",
    "churn",
    "signups",
    "how are things going this month",
    "enterprise breakdown",
    "what changed recently",
    "generate a marketing email for our pro plan",
]


def main() -> None:
    for q in QUESTIONS:
        r = should_execute(q)
        print(
            json.dumps(
                {
                    "question": q,
                    "recommendation": r["recommendation"],
                    "confidence": round(r["confidence"], 3),
                    "dimensions": {k: round(v, 3) for k, v in r["dimensions"].items()},
                }
            )
        )


if __name__ == "__main__":
    main()

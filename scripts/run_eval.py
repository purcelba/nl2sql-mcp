"""Run the labeled eval set through should_execute and print a confusion matrix."""

import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcp_server.server import should_execute  # noqa: E402

EVAL_PATH = ROOT / "semantic" / "eval_questions.yml"
LABELS = ["proceed", "clarify", "reject"]


def main() -> None:
    with EVAL_PATH.open() as f:
        items = yaml.safe_load(f)["questions"]

    rows = []
    for item in items:
        q = item["question"]
        expected = item["expected"]
        result = should_execute(q)
        rows.append(
            {
                "question": q,
                "expected": expected,
                "actual": result["recommendation"],
                "confidence": result["confidence"],
                "dimensions": result["dimensions"],
            }
        )
        print(
            f"[{expected:8s} -> {result['recommendation']:8s}] "
            f"conf={result['confidence']:.2f}  {q}"
        )

    print()
    print("## Confusion matrix")
    matrix: Counter = Counter()
    for r in rows:
        matrix[(r["expected"], r["actual"])] += 1

    header = f"{'expected \\ actual':>20s} | " + " | ".join(f"{a:>8s}" for a in LABELS)
    print(header)
    print("-" * len(header))
    for exp in LABELS:
        row = f"{exp:>20s} | " + " | ".join(
            f"{matrix[(exp, act)]:>8d}" for act in LABELS
        )
        print(row)

    correct = sum(matrix[(lbl, lbl)] for lbl in LABELS)
    print()
    print(f"Accuracy: {correct}/{len(rows)} = {correct / len(rows):.1%}")


if __name__ == "__main__":
    main()

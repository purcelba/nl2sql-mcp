"""End-to-end walkthrough: for a list of questions, gate -> generate SQL -> execute."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from anthropic import Anthropic  # noqa: E402

from mcp_server.scorers.sql_complexity import _generate_sql  # noqa: E402
from mcp_server.server import should_execute  # noqa: E402
from run_sql import connect, print_table  # noqa: E402

QUESTIONS = [
    "what is the mrr this quarter",
    "count of subscriptions by plan type",
    "how many events happened yesterday by event type",
]


def main() -> None:
    client = Anthropic()
    for q in QUESTIONS:
        print("=" * 80)
        print(f"Q: {q}")
        print("=" * 80)

        decision = should_execute(q)
        print(
            f"gate: recommendation={decision['recommendation']}, "
            f"confidence={decision['confidence']:.2f}"
        )
        if decision["recommendation"] != "proceed":
            print(f"skipping — {decision['next_step']}")
            continue

        sql = _generate_sql(q, client)
        print("\nGenerated SQL:")
        print(sql)

        print("\nResult:")
        try:
            with connect() as conn, conn.cursor() as cur:
                cur.execute(sql)
                if cur.description is None:
                    print(f"(no rows returned; {cur.rowcount} affected)")
                else:
                    columns = [d.name for d in cur.description]
                    rows = cur.fetchall()
                    print_table(columns, rows)
        except Exception as e:  # noqa: BLE001
            print(f"SQL execution failed: {e}")
        print()


if __name__ == "__main__":
    main()

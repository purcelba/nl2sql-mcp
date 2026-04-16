"""Execute a SQL query against local Postgres and print results as a table.

Usage:
    .venv/bin/python scripts/run_sql.py "SELECT COUNT(*) FROM dim_users"
    echo "SELECT 1" | .venv/bin/python scripts/run_sql.py
"""

import os
import sys

import psycopg


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "nl2sql"),
        user=os.getenv("PGUSER", "nl2sql"),
        password=os.getenv("PGPASSWORD", "nl2sql"),
    )


def print_table(columns: list[str], rows: list[tuple]) -> None:
    if not rows:
        print("(no rows)")
        return
    str_rows = [[str(v) if v is not None else "NULL" for v in r] for r in rows]
    widths = [
        max(len(columns[i]), *(len(r[i]) for r in str_rows)) for i in range(len(columns))
    ]
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*columns))
    print("-+-".join("-" * w for w in widths))
    for r in str_rows:
        print(fmt.format(*r))
    print(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main() -> None:
    if len(sys.argv) > 1:
        sql = " ".join(sys.argv[1:])
    else:
        sql = sys.stdin.read()
    sql = sql.strip()
    if not sql:
        print("error: no SQL provided", file=sys.stderr)
        sys.exit(1)
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        if cur.description is None:
            print(f"OK ({cur.rowcount} row{'s' if cur.rowcount != 1 else ''} affected)")
            return
        columns = [d.name for d in cur.description]
        rows = cur.fetchall()
        print_table(columns, rows)


if __name__ == "__main__":
    main()

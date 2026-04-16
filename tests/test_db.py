"""Smoke tests that connect to the local Postgres container.

Marked `db` — skipped by default. Run with:
    .venv/bin/python -m pytest tests/test_db.py --run-db
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest

from run_sql import connect

pytestmark = pytest.mark.db


def test_tables_exist():
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        tables = {r[0] for r in cur.fetchall()}
    assert {"dim_users", "fct_subscriptions", "fct_events"}.issubset(tables)


def test_seed_populated():
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM dim_users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fct_subscriptions")
        subs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fct_events")
        events = cur.fetchone()[0]
    assert users > 0, "run `python db/seed.py`"
    assert subs > 0
    assert events > 0


def test_plan_type_distribution():
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT plan_type FROM dim_users GROUP BY plan_type"
        )
        plans = {r[0] for r in cur.fetchall()}
    assert plans == {"free", "pro", "enterprise"}

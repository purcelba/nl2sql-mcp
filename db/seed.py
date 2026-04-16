"""Seed the local Postgres with realistic SaaS data.

Run once after `docker compose up -d`. Re-running wipes and re-seeds.
Connects to localhost:5432 by default; override via env vars.
"""

import os
import random
from datetime import date, datetime, timedelta

import psycopg

NUM_USERS = 500
NUM_SUBSCRIPTIONS = 800
NUM_EVENTS = 5_000

PLANS = ["free", "pro", "enterprise"]
PLAN_WEIGHTS = [0.60, 0.30, 0.10]
PLAN_MRR = {"free": 0, "pro": 29, "enterprise": 299}
COUNTRIES = ["US", "GB", "DE", "FR", "BR", "IN", "JP", "AU", "CA", "ES"]
EVENT_TYPES = ["login", "view_dashboard", "run_query", "export_csv", "invite_user"]

TODAY = date(2026, 4, 16)
SIGNUP_WINDOW_DAYS = 730  # last 2 years


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "nl2sql"),
        user=os.getenv("PGUSER", "nl2sql"),
        password=os.getenv("PGPASSWORD", "nl2sql"),
    )


def wipe(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE fct_events, fct_subscriptions, dim_users RESTART IDENTITY CASCADE")
    conn.commit()


def seed_users(conn: psycopg.Connection, rng: random.Random) -> list[tuple[int, date, str]]:
    users: list[tuple[int, date, str, str]] = []
    for uid in range(1, NUM_USERS + 1):
        days_ago = rng.randint(0, SIGNUP_WINDOW_DAYS)
        signup = TODAY - timedelta(days=days_ago)
        plan = rng.choices(PLANS, weights=PLAN_WEIGHTS)[0]
        country = rng.choice(COUNTRIES)
        users.append((uid, signup, plan, country))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO dim_users (user_id, signup_date, plan_type, country) VALUES (%s, %s, %s, %s)",
            users,
        )
    conn.commit()
    return [(u[0], u[1], u[2]) for u in users]


def seed_subscriptions(
    conn: psycopg.Connection, rng: random.Random, users: list[tuple[int, date, str]]
) -> None:
    rows = []
    sub_id = 1
    while len(rows) < NUM_SUBSCRIPTIONS:
        uid, signup, plan = rng.choice(users)
        # Skip free users roughly half the time (fewer of them subscribe)
        if plan == "free" and rng.random() < 0.5:
            continue
        started = signup + timedelta(days=rng.randint(0, 30))
        if started > TODAY:
            continue
        is_trial = rng.random() < 0.20
        # 30% of subscriptions have ended (churn)
        ended = None
        if rng.random() < 0.30:
            duration = rng.randint(30, 540)
            end = started + timedelta(days=duration)
            if end <= TODAY:
                ended = end
        mrr = PLAN_MRR[plan] if not is_trial else 0
        rows.append((sub_id, uid, plan, started, ended, is_trial, mrr))
        sub_id += 1
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO fct_subscriptions "
            "(subscription_id, user_id, plan_type, started_at, ended_at, is_trial, monthly_recurring_revenue) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            rows,
        )
    conn.commit()


def seed_events(
    conn: psycopg.Connection, rng: random.Random, users: list[tuple[int, date, str]]
) -> None:
    rows = []
    window_start = TODAY - timedelta(days=90)
    for ev_id in range(1, NUM_EVENTS + 1):
        uid, _, _ = rng.choice(users)
        offset_days = rng.randint(0, 90)
        ev_day = window_start + timedelta(days=offset_days)
        ts = datetime.combine(ev_day, datetime.min.time()) + timedelta(
            seconds=rng.randint(0, 86_399)
        )
        ev_type = rng.choice(EVENT_TYPES)
        rows.append((ev_id, uid, ts, ev_type))
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO fct_events (event_id, user_id, event_timestamp, event_type) VALUES (%s, %s, %s, %s)",
            rows,
        )
    conn.commit()


def main() -> None:
    rng = random.Random(42)
    with connect() as conn:
        wipe(conn)
        users = seed_users(conn, rng)
        seed_subscriptions(conn, rng, users)
        seed_events(conn, rng, users)
        with conn.cursor() as cur:
            for tbl in ("dim_users", "fct_subscriptions", "fct_events"):
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                print(f"{tbl}: {cur.fetchone()[0]}")


if __name__ == "__main__":
    main()

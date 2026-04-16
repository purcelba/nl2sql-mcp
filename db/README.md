# Local Postgres for NL2SQL testing

A Postgres 16 instance with a schema that mirrors `semantic/saas_metrics.yml`.
Init scripts in this directory are auto-loaded the first time the container
starts. To re-seed after changing them, tear down the volume with
`docker compose down -v`.

## Connection

- Host: `localhost`
- Port: `5432`
- Database: `nl2sql`
- User: `nl2sql`
- Password: `nl2sql`

## Usage

```bash
# Start (first run applies schema only)
docker compose up -d

# Seed ~500 users / 800 subs / 5k events (idempotent — wipes + re-seeds)
.venv/bin/python db/seed.py

# Shell into psql
docker compose exec postgres psql -U nl2sql -d nl2sql

# Stop (keeps data)
docker compose down

# Stop and wipe data (forces re-seed on next up)
docker compose down -v
```

## Running the db-backed tests

DB tests are marked `@pytest.mark.db` and skipped by default. To run them:

```bash
# Requires: docker compose up -d  AND  python db/seed.py
.venv/bin/python -m pytest --run-db
```

## Tables

- `dim_users` — one row per user (user_id, signup_date, plan_type, country)
- `fct_subscriptions` — one row per subscription period (incl. is_trial,
  monthly_recurring_revenue)
- `fct_events` — one row per product event (event_timestamp, event_type)

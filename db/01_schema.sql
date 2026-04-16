-- Schema mirroring semantic/saas_metrics.yml

CREATE TABLE dim_users (
    user_id      BIGINT PRIMARY KEY,
    signup_date  DATE NOT NULL,
    plan_type    TEXT NOT NULL CHECK (plan_type IN ('free', 'pro', 'enterprise')),
    country      TEXT NOT NULL
);

CREATE TABLE fct_subscriptions (
    subscription_id            BIGINT PRIMARY KEY,
    user_id                    BIGINT NOT NULL REFERENCES dim_users(user_id),
    plan_type                  TEXT NOT NULL CHECK (plan_type IN ('free', 'pro', 'enterprise')),
    started_at                 DATE NOT NULL,
    ended_at                   DATE,
    is_trial                   BOOLEAN NOT NULL DEFAULT FALSE,
    monthly_recurring_revenue  NUMERIC(10, 2) NOT NULL DEFAULT 0
);

CREATE TABLE fct_events (
    event_id         BIGINT PRIMARY KEY,
    user_id          BIGINT NOT NULL REFERENCES dim_users(user_id),
    event_timestamp  TIMESTAMP NOT NULL,
    event_type       TEXT NOT NULL
);

CREATE INDEX idx_fct_events_user_id ON fct_events(user_id);
CREATE INDEX idx_fct_events_timestamp ON fct_events(event_timestamp);
CREATE INDEX idx_fct_subscriptions_user_id ON fct_subscriptions(user_id);

"""SQL complexity scorer: generate SQL via Haiku, score by structural features."""

import re

from anthropic import Anthropic

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You generate a single Postgres SQL query that answers the \
user's question against a SaaS analytics warehouse. Return ONLY the SQL, no \
prose, no markdown fences.

Tables and columns:
- dim_users(user_id BIGINT, signup_date DATE, plan_type TEXT, country TEXT)
- fct_subscriptions(subscription_id BIGINT, user_id BIGINT, plan_type TEXT,
  started_at DATE, ended_at DATE, is_trial BOOLEAN,
  monthly_recurring_revenue NUMERIC)
- fct_events(event_id BIGINT, user_id BIGINT, event_timestamp TIMESTAMP,
  event_type TEXT)

Use CURRENT_DATE for "today". A subscription is active when ended_at IS NULL.

Semantic metrics (for reference only; column names above are authoritative):
{metrics}
Dimensions: {dimensions}
Entities: {entities}"""


def _generate_sql(question: str, client: Anthropic) -> str:
    system = SYSTEM_PROMPT.format(
        metrics=", ".join(get_all_metrics()),
        dimensions=", ".join(get_all_dimensions()),
        entities=", ".join(get_all_entities()),
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return _strip_fences(resp.content[0].text.strip())


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _score_sql(sql: str) -> tuple[float, dict]:
    s = sql.lower()
    features = {
        "joins": len(re.findall(r"\bjoin\b", s)),
        "subqueries": s.count("select") - 1 if s.count("select") > 1 else 0,
        "window_functions": len(re.findall(r"\bover\s*\(", s)),
        "group_bys": len(re.findall(r"\bgroup\s+by\b", s)),
        "ctes": len(re.findall(r"\bwith\b\s+\w+\s+as\s*\(", s)),
    }
    penalty = (
        0.10 * features["joins"]
        + 0.15 * features["subqueries"]
        + 0.20 * features["window_functions"]
        + 0.05 * features["group_bys"]
        + 0.10 * features["ctes"]
    )
    score = max(0.0, 1.0 - penalty)
    return score, features


def score_sql_complexity(question: str, client: Anthropic | None = None) -> dict:
    client = client or Anthropic()
    sql = _generate_sql(question, client)
    score, features = _score_sql(sql)
    return {
        "score": score,
        "features": features,
        "sql": sql,
        "reason": (
            f"generated SQL has joins={features['joins']}, "
            f"subqueries={features['subqueries']}, "
            f"window_functions={features['window_functions']}, "
            f"group_bys={features['group_bys']}, ctes={features['ctes']}"
        ),
    }

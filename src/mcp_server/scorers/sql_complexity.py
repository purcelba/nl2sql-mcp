"""SQL complexity scorer: generate SQL via Haiku, score by structural features."""

import re

from anthropic import Anthropic

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You generate a single SQL query that answers the user's question \
against a SaaS analytics warehouse. Return ONLY the SQL, no prose, no markdown fences.

Available metrics: {metrics}
Available dimensions: {dimensions}
Available entities: {entities}

Assume tables: dim_users, fct_events, fct_subscriptions. Keep the query realistic."""


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
    return resp.content[0].text.strip()


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

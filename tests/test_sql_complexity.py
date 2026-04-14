import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.scorers.sql_complexity import _score_sql, score_sql_complexity


class FakeClient:
    def __init__(self, sql: str):
        self._sql = sql
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(text=self._sql)])


def test_simple_select_is_high_confidence():
    score, feat = _score_sql("SELECT COUNT(*) FROM dim_users")
    assert score >= 0.9
    assert feat["joins"] == 0


def test_many_joins_and_windows_lower_confidence():
    sql = """
    WITH ranked AS (
      SELECT u.user_id, ROW_NUMBER() OVER (PARTITION BY u.plan_type ORDER BY s.started_at) AS rn
      FROM dim_users u
      JOIN fct_subscriptions s ON s.user_id = u.user_id
      JOIN fct_events e ON e.user_id = u.user_id
      WHERE s.started_at > (SELECT MIN(started_at) FROM fct_subscriptions)
    )
    SELECT plan_type, COUNT(*) FROM ranked GROUP BY plan_type
    """
    score, feat = _score_sql(sql)
    assert score < 0.6
    assert feat["joins"] >= 2
    assert feat["window_functions"] >= 1
    assert feat["ctes"] >= 1


def test_score_sql_complexity_uses_injected_client():
    client = FakeClient("SELECT COUNT(*) FROM dim_users WHERE plan_type = 'pro'")
    result = score_sql_complexity("how many pro users are there", client=client)
    assert result["score"] >= 0.9
    assert "sql" in result and "SELECT" in result["sql"]

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
    load_semantic_layer,
)


def test_load_returns_dict_with_expected_keys():
    layer = load_semantic_layer()
    assert "semantic_models" in layer
    assert "metrics" in layer


def test_metrics_include_expected_names():
    metrics = get_all_metrics()
    for expected in [
        "monthly_active_users",
        "churn_rate",
        "mrr",
        "trial_conversion_rate",
        "average_revenue_per_user",
    ]:
        assert expected in metrics


def test_dimensions_include_plan_type_and_event_type():
    dims = get_all_dimensions()
    assert "plan_type" in dims
    assert "event_type" in dims
    assert "signup_date" in dims
    assert "country" in dims


def test_entities_include_user_and_event_and_subscription():
    ents = get_all_entities()
    assert "user_id" in ents
    assert "event_id" in ents
    assert "subscription_id" in ents

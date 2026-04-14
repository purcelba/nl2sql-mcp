"""Load and query the dummy MetricFlow semantic layer."""

from pathlib import Path

import yaml

SEMANTIC_PATH = Path(__file__).resolve().parents[2] / "semantic" / "saas_metrics.yml"


def load_semantic_layer(path: Path = SEMANTIC_PATH) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)


_LAYER = load_semantic_layer()


def get_all_metrics() -> list[str]:
    return [m["name"] for m in _LAYER.get("metrics", [])]


def get_all_dimensions() -> list[str]:
    names: set[str] = set()
    for model in _LAYER.get("semantic_models", []):
        for dim in model.get("dimensions", []):
            names.add(dim["name"])
    return sorted(names)


def get_all_entities() -> list[str]:
    names: set[str] = set()
    for model in _LAYER.get("semantic_models", []):
        for ent in model.get("entities", []):
            names.add(ent["name"])
    return sorted(names)

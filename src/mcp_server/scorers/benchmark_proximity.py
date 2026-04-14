"""Benchmark proximity scorer: cosine similarity to the nearest known-good question."""

from pathlib import Path

import yaml
from sentence_transformers import SentenceTransformer, util

BENCHMARK_PATH = Path(__file__).resolve().parents[3] / "semantic" / "benchmarks.yml"
MODEL_NAME = "all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None
_benchmarks: list[str] | None = None
_benchmark_embeddings = None


def _load() -> None:
    global _model, _benchmarks, _benchmark_embeddings
    if _model is not None:
        return
    _model = SentenceTransformer(MODEL_NAME)
    with BENCHMARK_PATH.open() as f:
        _benchmarks = yaml.safe_load(f)["questions"]
    _benchmark_embeddings = _model.encode(_benchmarks, convert_to_tensor=True)


def score_benchmark_proximity(question: str) -> dict:
    _load()
    q_emb = _model.encode(question, convert_to_tensor=True)
    sims = util.cos_sim(q_emb, _benchmark_embeddings)[0]
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])
    best_score = max(0.0, min(1.0, best_score))
    return {
        "score": best_score,
        "nearest": _benchmarks[best_idx],
        "reason": (
            f"nearest benchmark (cosine {best_score:.2f}): "
            f"'{_benchmarks[best_idx]}'"
        ),
    }

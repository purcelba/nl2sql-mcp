import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.scorers.llm_judge import _parse_response, score_llm_judge


class FakeClient:
    def __init__(self, text: str):
        self._text = text
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        return SimpleNamespace(content=[SimpleNamespace(text=self._text)])


def test_parse_valid_json():
    score, reason = _parse_response('{"score": 0.8, "reason": "clear mapping"}')
    assert score == 0.8
    assert "clear" in reason


def test_parse_clamps_out_of_range():
    score, _ = _parse_response('{"score": 1.5, "reason": "x"}')
    assert score == 1.0


def test_parse_handles_garbage():
    score, _ = _parse_response("no json here")
    assert score == 0.0


def test_score_llm_judge_uses_injected_client():
    client = FakeClient('{"score": 0.9, "reason": "mrr is available"}')
    result = score_llm_judge("what is mrr", client=client)
    assert result["score"] == 0.9
    assert "mrr" in result["reason"]

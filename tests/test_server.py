"""Direct tests for the mock MCP tools (Phase 1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_server.server import echo_confidence


def test_echo_confidence_shape():
    result = echo_confidence("how many users signed up last week?")
    assert result["confidence"] == 0.75
    assert isinstance(result["reasons"], list) and result["reasons"]
    assert result["question"] == "how many users signed up last week?"


def test_echo_confidence_is_constant():
    assert echo_confidence("a")["confidence"] == echo_confidence("b")["confidence"]



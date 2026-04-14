"""LLM-as-judge scorer: ask Haiku to rate answerability given the semantic layer."""

import json
import re

from anthropic import Anthropic

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You rate whether a natural-language analytics question can be \
answered using the available semantic layer. Respond with ONLY a JSON object of the form:
{{"score": <float 0-1>, "reason": "<one sentence>"}}

Score meaning:
- 1.0: question maps cleanly to the available metrics/dimensions/entities
- 0.5: partial mapping, likely answerable with assumptions
- 0.0: no reasonable mapping, question is out of scope

Available metrics: {metrics}
Available dimensions: {dimensions}
Available entities: {entities}"""


def _parse_response(text: str) -> tuple[float, str]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return 0.0, f"could not parse judge response: {text[:100]}"
    try:
        obj = json.loads(match.group(0))
        score = float(obj.get("score", 0.0))
        reason = str(obj.get("reason", ""))
        return max(0.0, min(1.0, score)), reason
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return 0.0, f"judge response parse error: {e}"


def score_llm_judge(question: str, client: Anthropic | None = None) -> dict:
    client = client or Anthropic()
    system = SYSTEM_PROMPT.format(
        metrics=", ".join(get_all_metrics()),
        dimensions=", ".join(get_all_dimensions()),
        entities=", ".join(get_all_entities()),
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    text = resp.content[0].text.strip()
    score, reason = _parse_response(text)
    return {"score": score, "reason": f"llm judge: {reason}", "raw": text}

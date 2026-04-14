"""Generate concrete rephrasing suggestions for ambiguous questions."""

import json
import re

from anthropic import Anthropic

from mcp_server.semantic_loader import (
    get_all_dimensions,
    get_all_entities,
    get_all_metrics,
)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You help users rephrase ambiguous analytics questions so they \
map cleanly onto an available semantic layer. Return ONLY a JSON array of 2-4 \
alternative questions as strings: ["...", "...", "..."].

Each suggestion must:
- be a concrete, well-formed analytics question
- reference specific metrics/dimensions from the semantic layer below
- include a time window or grouping when the original was vague

Available metrics: {metrics}
Available dimensions: {dimensions}
Available entities: {entities}"""


def _parse(text: str) -> list[str]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        arr = json.loads(match.group(0))
        return [str(s) for s in arr if isinstance(s, str) and s.strip()]
    except (json.JSONDecodeError, ValueError, TypeError):
        return []


def suggest_rephrases(
    question: str,
    dimensions: dict,
    nearest_benchmark: str | None = None,
    matched_terms: list[str] | None = None,
    unmatched_terms: list[str] | None = None,
    client: Anthropic | None = None,
) -> list[str]:
    client = client or Anthropic()
    system = SYSTEM_PROMPT.format(
        metrics=", ".join(get_all_metrics()),
        dimensions=", ".join(get_all_dimensions()),
        entities=", ".join(get_all_entities()),
    )
    context_lines = [f"Original question: {question}"]
    if nearest_benchmark:
        context_lines.append(f"Nearest known-good question: {nearest_benchmark}")
    if matched_terms is not None:
        context_lines.append(f"Terms that matched the semantic layer: {matched_terms}")
    if unmatched_terms is not None:
        context_lines.append(f"Terms that did not match: {unmatched_terms}")
    context_lines.append(
        f"Per-dimension scores: {dimensions}"
    )

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": "\n".join(context_lines)}],
        )
        return _parse(resp.content[0].text.strip())
    except Exception:
        return []

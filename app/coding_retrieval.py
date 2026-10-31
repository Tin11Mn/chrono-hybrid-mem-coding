"""Bounded, source-preserving views for ranking long engineering records."""

import re
from typing import Iterable


def _tokens(text: str) -> set:
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return set(re.findall(r"[^\W_]+", text.casefold(), re.UNICODE))


def evidence_excerpt(content: str, terms: Iterable[str], limit: int = 2400) -> str:
    """Select verbatim windows throughout a record, only for the model's view.

    Full source records remain the API response. Fixed windows also handle a
    single very long tool-output line, where paragraph-only splitting fails.
    """
    if len(content) <= limit:
        return content
    words = {
        token.casefold() for term in terms
        for token in _tokens(term) if len(token) >= 3
    }
    width = min(720, max(1, limit // 3))
    stride = max(1, width // 2)
    spans = []
    for start in range(0, len(content), stride):
        stop = min(len(content), start + width)
        tokens = _tokens(content[start:stop])
        spans.append((len(words & tokens), start, stop))
    selected = []
    used = 0
    # A marker is view metadata, never fabricated evidence or an API result.
    separator = "\n[... source gap ...]\n"
    for _, start, stop in sorted(spans, key=lambda item: (-item[0], item[1])):
        if any(start < old_stop and stop > old_start for old_start, old_stop in selected):
            continue
        cost = stop - start + (len(separator) if selected else 0)
        if used + cost > limit:
            continue
        selected.append((start, stop))
        used += cost
        if len(selected) == 3:
            break
    return separator.join(content[start:stop] for start, stop in sorted(selected))

"""entity_timeline — Dated mentions and facts for one entity or topic."""
from __future__ import annotations

import re
from typing import Any

from .. import _common
from ..activity_ledger import iter_markdown, note_date


def _snippet(text: str, needle: str, width: int = 220) -> str:
    haystack = text.lower()
    idx = haystack.find(needle.lower())
    if idx < 0:
        return ""
    start = max(0, idx - width // 2)
    end = min(len(text), idx + len(needle) + width // 2)
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def entity_timeline(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    query = str(kwargs.get("query") or "").strip()
    kind = str(kwargs.get("kind") or "").strip().lstrip("#")
    if not vault:
        return _common.error("missing 'vault'")
    if not query:
        return _common.error("missing 'query'")
    try:
        limit = max(1, min(int(kwargs.get("limit", 25)), 100))
    except (TypeError, ValueError):
        limit = 25

    vault_p = _common.resolve_vault_path(vault)
    needle = query.lower()
    entries: list[dict[str, Any]] = []

    for md in iter_markdown(vault_p, include_archive=True):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm, body = _common.split_frontmatter(text)
        fm = fm or {}
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        tags = [str(t).lstrip("#") for t in tags] if isinstance(tags, list) else []
        if kind and f"tars/{kind}" not in tags and kind not in tags:
            continue

        searchable = " ".join(
            [
                str(md.relative_to(vault_p)).lower(),
                str(fm.get("title") or fm.get("tars-name") or md.stem).lower(),
                str(fm).lower(),
                body.lower(),
            ]
        )
        wikilink_hit = f"[[{needle}" in body.lower() or f"[[{needle}" in text.lower()
        if needle not in searchable and not wikilink_hit:
            continue
        dt = note_date(md, fm)
        entries.append(
            {
                "path": str(md.relative_to(vault_p)).replace("\\", "/"),
                "title": fm.get("title") or fm.get("tars-name") or md.stem,
                "date": dt.isoformat() if dt else None,
                "tags": tags,
                "snippet": _snippet(body or text, query),
            }
        )

    entries.sort(key=lambda item: str(item.get("date") or ""), reverse=True)
    return _common.ok(query=query, kind=kind or None, count=len(entries), entries=entries[:limit])

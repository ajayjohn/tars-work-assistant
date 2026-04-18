"""search_by_tag — Find notes whose frontmatter `tags:` contains a given tag.

Walks the vault, parses frontmatter, matches tag. Stdlib-only, no index
required (FTS search.db does not cover the `tags` field).

Arguments:
  vault:  required.
  tag:    required. With or without leading `#`.
  limit:  optional (default 50, max 200).
  prefix_match: optional bool. If true, match any tag that starts with
                `tag` (so "tars/person" finds "tars/person/contractor").

Returns:
  {status: ok, results: [{path, tags, title?, frontmatter_summary}]}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common


SKIP_DIRS = {".git", ".obsidian", ".claude", "_system/embedding-cache"}


def _normalize(tag: str) -> str:
    return tag.lstrip("#").strip()


def search_by_tag(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    tag = kwargs.get("tag")
    limit = kwargs.get("limit", 50)
    prefix_match = bool(kwargs.get("prefix_match", False))

    if not vault:
        return _common.error("missing 'vault'")
    if not tag or not isinstance(tag, str):
        return _common.error("missing 'tag' (str)")
    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 50

    target = _normalize(tag)
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    results: list[dict[str, Any]] = []
    for md in vault_p.rglob("*.md"):
        rel = md.relative_to(vault_p)
        if any(str(rel).startswith(s) for s in SKIP_DIRS):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fm, _body = _common.split_frontmatter(text)
        if not fm:
            continue
        tags = fm.get("tags")
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            continue
        matched = False
        for t in tags:
            if not isinstance(t, str):
                continue
            nt = _normalize(t)
            if nt == target or (prefix_match and nt.startswith(target + "/")):
                matched = True
                break
        if not matched:
            continue
        results.append({
            "path": str(rel),
            "tags": tags,
            "title": fm.get("title") or md.stem,
        })
        if len(results) >= limit:
            break

    return _common.ok(tag=target, count=len(results), results=results)

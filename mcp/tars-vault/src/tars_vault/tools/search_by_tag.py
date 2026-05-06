"""search_by_tag — Find notes whose frontmatter `tags:` contains a given tag.

Walks the vault, parses frontmatter, matches tag. Stdlib-only, no index
required (FTS search.db does not cover the `tags` field).

Arguments:
  vault:       required.
  tag:         required. With or without leading `#`.
  query:       optional text filter across path, title, frontmatter, and body.
  frontmatter: optional mapping of frontmatter filters. Supports exact matches
               plus __gte, __lte, __gt, __lt, and __ne suffixes.
  limit:       optional (default 50, max 200).
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


def _as_search_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(f"{k} {_as_search_text(v)}" for k, v in value.items())
    if isinstance(value, list):
        return " ".join(_as_search_text(v) for v in value)
    return str(value)


def _scalar_values(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _compare(actual: Any, expected: Any, op: str) -> bool:
    values = _scalar_values(actual)
    if op == "eq":
        return any(v == expected or str(v).lower() == str(expected).lower() for v in values)
    if op == "ne":
        return all(v != expected and str(v).lower() != str(expected).lower() for v in values)
    for v in values:
        left = str(v)
        right = str(expected)
        if op == "gte" and left >= right:
            return True
        if op == "lte" and left <= right:
            return True
        if op == "gt" and left > right:
            return True
        if op == "lt" and left < right:
            return True
    return False


def _frontmatter_matches(fm: dict[str, Any], filters: Any) -> bool:
    if not filters:
        return True
    if not isinstance(filters, dict):
        return False
    for raw_key, expected in filters.items():
        key = str(raw_key)
        op = "eq"
        for suffix, mapped in (
            ("__gte", "gte"),
            ("__lte", "lte"),
            ("__gt", "gt"),
            ("__lt", "lt"),
            ("__ne", "ne"),
        ):
            if key.endswith(suffix):
                key = key[: -len(suffix)]
                op = mapped
                break
        if key not in fm or not _compare(fm.get(key), expected, op):
            return False
    return True


def search_by_tag(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    tag = kwargs.get("tag")
    query = kwargs.get("query")
    frontmatter_filter = kwargs.get("frontmatter")
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
        fm, body = _common.split_frontmatter(text)
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
        if not _frontmatter_matches(fm, frontmatter_filter):
            continue
        if query:
            needle = str(query).strip().lower()
            haystack = " ".join(
                [
                    str(rel).lower(),
                    str(fm.get("title") or md.stem).lower(),
                    _as_search_text(fm).lower(),
                    body.lower(),
                ]
            )
            if needle not in haystack:
                continue
        results.append({
            "path": str(rel),
            "tags": tags,
            "title": fm.get("title") or md.stem,
            "frontmatter_summary": {
                k: v for k, v in fm.items()
                if k in ("tars-date", "tars-status", "tars-owner", "tars-updated", "tars-due")
            },
        })
        if len(results) >= limit:
            break

    return _common.ok(tag=target, count=len(results), results=results)

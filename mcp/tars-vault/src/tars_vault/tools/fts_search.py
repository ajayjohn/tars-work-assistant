"""fts_search — BM25 keyword search against ``_system/search.db``.

Phase 4 implementation (PRD §6.5). Thin wrapper around
``tars_vault.search_index.fts_query`` — the tool's job is argument marshalling
and graceful degradation when the index has not yet been built.

Arguments:
  query:         required. Raw FTS5 query string.
  vault:         required. Absolute vault path.
  scope:         optional convenience — "memory" | "journal" | "transcripts"
                 | "contexts" | "all". Sets tier + source_types together so
                 skill prose can say `fts_search(scope="memory", …)`.
  tier:          optional. "A" | "B" | None (both). Wins over scope if set.
  source_types:  optional list — e.g. ["memory"], ["journal", "transcript"].
                 Wins over scope if set.
  limit:         optional. Default 10. Hard-capped to 50.

Returns:
  {"status": "ok",       "results": [...]}                — index present
  {"status": "no_index", "results": [], "reason": "..."}  — index missing
  {"status": "error",    "results": [], "reason": "..."}  — query failure
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import search_index as si


MAX_LIMIT = 50

SCOPE_TO_TIER = {
    "memory": ("A", ["memory"]),
    "journal": ("B", ["journal"]),
    "transcripts": ("B", ["transcript"]),
    "contexts": ("B", ["context"]),
    "all": (None, None),
}


def fts_search(**kwargs: Any) -> dict:
    query = kwargs.get("query")
    vault = kwargs.get("vault")
    if not query or not isinstance(query, str):
        return {"status": "error", "results": [], "reason": "missing 'query' (str)"}
    if not vault:
        return {"status": "error", "results": [], "reason": "missing 'vault' path"}

    vault_path = Path(vault).expanduser()
    db_path = si.index_path(vault_path)
    if not db_path.is_file():
        return {
            "status": "no_index",
            "results": [],
            "reason": f"index not built yet at {db_path} — run scripts/build-search-index.py --apply",
        }

    scope = kwargs.get("scope")
    tier = kwargs.get("tier")
    source_types = kwargs.get("source_types") or None

    if scope is not None:
        if scope not in SCOPE_TO_TIER:
            return {
                "status": "error",
                "results": [],
                "reason": f"scope must be one of {sorted(SCOPE_TO_TIER)}",
            }
        scope_tier, scope_sources = SCOPE_TO_TIER[scope]
        if tier is None:
            tier = scope_tier
        if source_types is None:
            source_types = scope_sources

    if tier not in (None, "A", "B"):
        return {"status": "error", "results": [], "reason": "tier must be 'A' or 'B'"}
    if source_types is not None and not isinstance(source_types, (list, tuple)):
        return {"status": "error", "results": [], "reason": "source_types must be a list"}

    limit = kwargs.get("limit", 10)
    try:
        limit = max(1, min(int(limit), MAX_LIMIT))
    except (TypeError, ValueError):
        limit = 10

    conn, _ = si.open_index(db_path, load_vec=False)
    try:
        rows = si.fts_query(
            conn, query, tier=tier, source_types=source_types, limit=limit
        )
    except Exception as exc:
        conn.close()
        return {"status": "error", "results": [], "reason": f"fts query failed: {exc}"}
    conn.close()
    return {"status": "ok", "results": rows, "count": len(rows)}

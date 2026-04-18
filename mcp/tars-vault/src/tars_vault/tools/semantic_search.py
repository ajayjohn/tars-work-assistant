"""semantic_search — hybrid retrieval over long prose (Tier B).

Phase 4 implementation (PRD §6.1, §6.5, §26.12).

Runs FastEmbed (``BAAI/bge-small-en-v1.5`` by default, fallback
``sentence-transformers/all-MiniLM-L6-v2``) on the query, KNN-searches
``vec_chunks``, and linearly merges those hits with FTS5 results from the same
scope using the hybrid 0.7 × semantic + 0.3 × FTS weighting specified in §6.1.

Arguments:
  query:        required. Natural-language query.
  vault:        required. Absolute vault path.
  scope:        optional. One of "journal" | "transcripts" | "contexts" | "all".
                Defaults to "all" (Tier B).
  top_k:        optional. Default 10. Hard-capped to 50.
  date_range:   optional {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}. Applied
                post-query to chunk metadata.

Returns:
  {"status": "ok",        "results": [...], "fallback": null}
  {"status": "no_index",  "results": [], "reason": "..."}
  {"status": "fts_only",  "results": [...], "fallback": "fts_only",
    "reason": "..."}  — semantic layer unavailable; caller should note the gap.
  {"status": "error",     "results": [], "reason": "..."}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import search_index as si


MAX_K = 50
SEMANTIC_WEIGHT = 0.7
FTS_WEIGHT = 0.3

SCOPE_TO_SOURCE_TYPES = {
    "journal": ["journal"],
    "transcripts": ["transcript"],
    "contexts": ["context"],
    "all": ["journal", "transcript", "context"],
}


def semantic_search(**kwargs: Any) -> dict:
    query = kwargs.get("query")
    vault = kwargs.get("vault")
    if not query or not isinstance(query, str):
        return {"status": "error", "results": [], "reason": "missing 'query' (str)"}
    if not vault:
        return {"status": "error", "results": [], "reason": "missing 'vault' path"}

    scope = kwargs.get("scope", "all")
    if scope not in SCOPE_TO_SOURCE_TYPES:
        return {
            "status": "error",
            "results": [],
            "reason": f"scope must be one of {sorted(SCOPE_TO_SOURCE_TYPES)}",
        }
    source_types = SCOPE_TO_SOURCE_TYPES[scope]

    top_k = kwargs.get("top_k", 10)
    try:
        top_k = max(1, min(int(top_k), MAX_K))
    except (TypeError, ValueError):
        top_k = 10

    date_range = kwargs.get("date_range")

    vault_path = Path(vault).expanduser()
    db_path = si.index_path(vault_path)
    if not db_path.is_file():
        return {
            "status": "no_index",
            "results": [],
            "reason": f"index not built yet at {db_path} — run scripts/build-search-index.py --apply",
        }

    conn, vec_enabled = si.open_index(db_path, load_vec=True)
    try:
        fts_rows = _safe_fts(conn, query, source_types, top_k * 2)
        sem_rows: list[dict] = []
        fallback = None
        if vec_enabled:
            try:
                embedder = _load_embedder(vault_path)
                if embedder is None:
                    fallback = "fts_only"
                else:
                    query_vec = embedder.embed([query])[0]
                    sem_rows = si.semantic_query(
                        conn, query_vec,
                        source_types=source_types, limit=top_k * 2,
                    )
            except Exception as exc:
                fallback = "fts_only"
                fallback_reason = f"semantic layer error: {exc}"
        else:
            fallback = "fts_only"
            fallback_reason = "sqlite-vec extension unavailable"
    finally:
        conn.close()

    if date_range:
        fts_rows = _filter_date(fts_rows, date_range)
        sem_rows = _filter_date(sem_rows, date_range)

    merged = _merge(sem_rows, fts_rows, top_k)
    if fallback == "fts_only":
        return {
            "status": "fts_only",
            "results": merged,
            "fallback": "fts_only",
            "reason": locals().get("fallback_reason", "semantic layer unavailable"),
            "count": len(merged),
        }
    return {"status": "ok", "results": merged, "fallback": None, "count": len(merged)}


def _safe_fts(conn, query: str, source_types, limit: int) -> list[dict]:
    try:
        return si.fts_query(
            conn, query, tier="B", source_types=source_types, limit=limit
        )
    except Exception:
        return []


def _load_embedder(vault_path: Path):
    """Lazy-load a FastEmbed model. Returns None if unavailable."""
    try:
        from fastembed import TextEmbedding  # type: ignore
    except Exception:
        return None
    cache = vault_path / "_system" / "embedding-cache"
    try:
        return TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=str(cache))
    except Exception:
        try:
            return TextEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                cache_dir=str(cache),
            )
        except Exception:
            return None


def _filter_date(rows: list[dict], date_range: dict) -> list[dict]:
    start = date_range.get("start")
    end = date_range.get("end")
    out: list[dict] = []
    for row in rows:
        date = row.get("date") or ""
        if start and date < start:
            continue
        if end and date > end:
            continue
        out.append(row)
    return out


def _merge(sem: list[dict], fts: list[dict], top_k: int) -> list[dict]:
    """Hybrid merge per PRD §6.1 (0.7 semantic + 0.3 FTS).

    FTS5 bm25 is lower = better (we negate and min-max normalise). sqlite-vec
    distance is lower = better (likewise). Chunked Tier-B FTS may match a whole
    document; we key on (path, chunk_index). Documents without a chunk match
    from FTS are keyed on (path, None) and contribute their doc-level score.
    """
    scores: dict[tuple[str, int | None], dict] = {}

    if sem:
        sem_norm = _normalise([-r["distance"] for r in sem])
        for row, s in zip(sem, sem_norm):
            key = (row["path"], row["chunk_index"])
            scores[key] = {
                **row,
                "semantic_score": s,
                "fts_score": 0.0,
                "hybrid_score": SEMANTIC_WEIGHT * s,
            }

    if fts:
        fts_norm = _normalise([-r["score"] for r in fts])
        for row, s in zip(fts, fts_norm):
            key = (row["path"], None)
            if key in scores:
                scores[key]["fts_score"] = s
                scores[key]["hybrid_score"] += FTS_WEIGHT * s
            else:
                # Propagate FTS score to every chunk of this path already scored
                # via semantic. If none, surface the doc-level FTS snippet alone.
                chunk_keys = [k for k in scores if k[0] == row["path"]]
                if chunk_keys:
                    for k in chunk_keys:
                        scores[k]["fts_score"] = s
                        scores[k]["hybrid_score"] += FTS_WEIGHT * s
                        scores[k].setdefault("snippet", row.get("snippet"))
                else:
                    scores[key] = {
                        "path": row["path"],
                        "chunk_index": None,
                        "text": row.get("snippet", ""),
                        "source_type": row.get("source_type"),
                        "date": row.get("date"),
                        "snippet": row.get("snippet"),
                        "semantic_score": 0.0,
                        "fts_score": s,
                        "hybrid_score": FTS_WEIGHT * s,
                    }

    ranked = sorted(scores.values(), key=lambda r: r["hybrid_score"], reverse=True)
    return ranked[:top_k]


def _normalise(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [1.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]

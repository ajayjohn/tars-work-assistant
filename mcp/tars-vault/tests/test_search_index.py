"""Unit tests for the search_index module and the Phase 4 MCP tools.

Exercise the stdlib-only paths. sqlite-vec and FastEmbed are optional — tests
fall back cleanly when either is unavailable, and assert the tool contracts
hold in both modes.

Run: python3 mcp/tars-vault/tests/test_search_index.py
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Bootstrap path (conftest-style).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tars_vault import search_index as si  # noqa: E402
from tars_vault.tools import fts_search, semantic_search, rerank  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Tier / path helpers
# ---------------------------------------------------------------------------

def test_classify_tier() -> None:
    _assert(si.classify_tier("memory/people/jane.md") == "A", "memory must be Tier A")
    _assert(si.classify_tier("journal/2026-04/2026-04-17-sync.md") == "B", "journal is Tier B")
    _assert(si.classify_tier("archive/transcripts/2026-04/foo.md") == "B", "transcripts is Tier B")
    _assert(si.classify_tier("contexts/products/widget.md") == "B", "contexts is Tier B")
    _assert(si.classify_tier("tasks/2026-04-17-todo.md") is None, "tasks excluded from hybrid index")
    _assert(si.classify_tier("_system/config.md") is None, "_system excluded")


def test_source_type_mapping() -> None:
    _assert(si.source_type_for("memory/people/jane.md") == "memory", "memory mapping")
    _assert(si.source_type_for("journal/2026-04/x.md") == "journal", "journal mapping")
    _assert(si.source_type_for("archive/transcripts/2026-04/t.md") == "transcript", "transcript mapping")
    _assert(si.source_type_for("contexts/products/w.md") == "context", "context mapping")


# ---------------------------------------------------------------------------
# Frontmatter + chunking
# ---------------------------------------------------------------------------

def test_split_frontmatter_and_title() -> None:
    text = """---
tags: [tars/journal, tars/meeting]
tars-date: 2026-04-17
---

# Q1 Planning Sync

Body text here.
"""
    fm, body = si.split_frontmatter(text)
    _assert("tars-date: 2026-04-17" in fm, "frontmatter captured")
    _assert(body.lstrip().startswith("# Q1"), f"body starts with title heading, got: {body[:30]!r}")
    _assert(si.extract_title(Path("foo.md"), body) == "Q1 Planning Sync", "title extracted")
    tags = si.extract_tags(fm)
    _assert("tars/journal" in tags and "tars/meeting" in tags, f"tags parsed: {tags}")
    _assert(si.extract_date(fm, "journal/2026-04/foo.md") == "2026-04-17", "date from frontmatter")


def test_extract_date_from_path() -> None:
    _assert(si.extract_date("", "journal/2026-04/2026-04-17-sync.md") == "2026-04-17",
            "date fallback from path")


def test_chunk_body_short_and_long() -> None:
    short = "one two three"
    chunks = si.chunk_body(short)
    _assert(len(chunks) == 1 and chunks[0].text == short, f"short body → 1 chunk: {chunks}")

    words = [f"w{i}" for i in range(850)]
    long_body = " ".join(words)
    long_chunks = si.chunk_body(long_body, chunk_words=300, overlap_words=60)
    _assert(len(long_chunks) >= 3, f"long body should produce multiple chunks: got {len(long_chunks)}")
    _assert(long_chunks[0].index == 0, "first chunk index 0")
    first_words = long_chunks[0].text.split()
    second_words = long_chunks[1].text.split()
    _assert(first_words[-60:] == second_words[:60], "adjacent chunks must overlap by overlap_words")


def test_chunk_body_empty() -> None:
    _assert(si.chunk_body("") == [], "empty body produces no chunks")
    _assert(si.chunk_body("   \n\t  ") == [], "whitespace-only body produces no chunks")


# ---------------------------------------------------------------------------
# Schema init + FTS round-trip (no vec extension required)
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "search.db"
    conn, _ = si.open_index(db_path, load_vec=False)
    si.init_schema(conn, vec_enabled=False)
    return conn


def test_schema_and_fts_roundtrip(tmp_path: Path) -> None:
    conn = _fresh_db(tmp_path)
    try:
        note = si.NoteRecord(
            path="memory/people/jane-smith.md",
            title="Jane Smith",
            tags=["tars/person"],
            body="Jane leads platform and mobile at CSI. Reports to the CTO.",
            tier="A",
            source_type="memory",
            date="2026-03-15",
        )
        si.upsert_note_fts(conn, note)
        conn.commit()
        rows = si.fts_query(conn, "platform", tier="A", limit=5)
        _assert(rows and rows[0]["path"] == note.path, f"FTS should find note: {rows}")
        _assert(rows[0]["tier"] == "A", "tier echoed")
        _assert("snippet" in rows[0] and "<<<" in rows[0]["snippet"], f"snippet: {rows[0].get('snippet')}")
    finally:
        conn.close()


def test_delete_path_clears_fts(tmp_path: Path) -> None:
    conn = _fresh_db(tmp_path)
    try:
        note = si.NoteRecord(path="journal/2026-04/sync.md", title="Sync", body="alpha beta", tier="B", source_type="journal")
        si.upsert_note_fts(conn, note)
        conn.commit()
        _assert(len(si.fts_query(conn, "alpha", limit=5)) == 1, "insert visible")
        si.delete_path(conn, note.path, vec_enabled=False)
        conn.commit()
        _assert(si.fts_query(conn, "alpha", limit=5) == [], "delete clears FTS rows")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool contracts
# ---------------------------------------------------------------------------

def test_fts_search_no_index(tmp_path: Path) -> None:
    out = fts_search.fts_search(query="anything", vault=str(tmp_path))
    _assert(out["status"] == "no_index", f"expected no_index, got {out}")
    _assert(out["results"] == [], "no_index must return empty results")


def test_fts_search_missing_args() -> None:
    out = fts_search.fts_search(query="foo")
    _assert(out["status"] == "error" and "vault" in out["reason"], f"vault missing: {out}")
    out = fts_search.fts_search(vault="/tmp")
    _assert(out["status"] == "error" and "query" in out["reason"], f"query missing: {out}")


def test_fts_search_with_built_index(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "_system").mkdir(parents=True)
    db_path = si.index_path(vault)
    conn, _ = si.open_index(db_path, load_vec=False)
    si.init_schema(conn, vec_enabled=False)
    si.upsert_note_fts(conn, si.NoteRecord(
        path="memory/people/jane.md", title="Jane", tags=["tars/person"],
        body="platform lead", tier="A", source_type="memory", date="2026-03-01",
    ))
    conn.commit()
    conn.close()

    out = fts_search.fts_search(query="platform", vault=str(vault), tier="A", limit=5)
    _assert(out["status"] == "ok", f"expected ok, got {out}")
    _assert(out["count"] == 1 and out["results"][0]["path"] == "memory/people/jane.md",
            f"expected one hit, got {out}")


def test_fts_search_scope_alias(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    (vault / "_system").mkdir(parents=True)
    db_path = si.index_path(vault)
    conn, _ = si.open_index(db_path, load_vec=False)
    si.init_schema(conn, vec_enabled=False)
    si.upsert_note_fts(conn, si.NoteRecord(
        path="memory/people/jane.md", title="Jane", body="platform lead",
        tier="A", source_type="memory",
    ))
    si.upsert_note_fts(conn, si.NoteRecord(
        path="journal/2026-04/sync.md", title="Sync", body="platform rollout",
        tier="B", source_type="journal",
    ))
    conn.commit()
    conn.close()

    out = fts_search.fts_search(query="platform", vault=str(vault), scope="memory")
    _assert(out["status"] == "ok", f"scope=memory status: {out}")
    _assert(all(r["source_type"] == "memory" for r in out["results"]),
            f"scope=memory filtered results: {out}")

    out2 = fts_search.fts_search(query="platform", vault=str(vault), scope="journal")
    _assert(all(r["source_type"] == "journal" for r in out2["results"]),
            f"scope=journal filtered results: {out2}")

    out3 = fts_search.fts_search(query="bogus", vault=str(vault), scope="not-a-scope")
    _assert(out3["status"] == "error", f"invalid scope: {out3}")


def test_semantic_search_no_index(tmp_path: Path) -> None:
    out = semantic_search.semantic_search(query="how is the rewrite going?", vault=str(tmp_path))
    _assert(out["status"] == "no_index", f"expected no_index, got {out}")


def test_semantic_search_fallback_when_vec_unavailable(tmp_path: Path) -> None:
    """When vec is unavailable the tool still returns FTS-only results."""
    vault = tmp_path / "vault"
    (vault / "_system").mkdir(parents=True)
    db_path = si.index_path(vault)
    # Open WITHOUT loading the vec extension so schema is FTS-only.
    conn, _ = si.open_index(db_path, load_vec=False)
    si.init_schema(conn, vec_enabled=False)
    si.upsert_note_fts(conn, si.NoteRecord(
        path="journal/2026-04/sync.md", title="Q1 Sync", tags=["tars/journal"],
        body="discussed the rewrite timeline at length",
        tier="B", source_type="journal", date="2026-04-17",
    ))
    conn.commit()
    conn.close()

    out = semantic_search.semantic_search(query="rewrite", vault=str(vault), scope="journal")
    _assert(out["status"] in ("fts_only", "ok"), f"status: {out['status']}")
    if out["status"] == "fts_only":
        _assert(out["fallback"] == "fts_only", "fallback flag set")


def test_semantic_search_invalid_scope(tmp_path: Path) -> None:
    out = semantic_search.semantic_search(query="x", vault=str(tmp_path), scope="bogus")
    _assert(out["status"] == "error" and "scope" in out["reason"], f"scope validation: {out}")


# ---------------------------------------------------------------------------
# rerank
# ---------------------------------------------------------------------------

def test_rerank_orders_by_hybrid_score() -> None:
    out = rerank.rerank(
        candidates=[
            {"path": "a", "hybrid_score": 0.5, "source_type": "context", "date": "2020-01-01"},
            {"path": "b", "hybrid_score": 0.8, "source_type": "context", "date": "2020-01-01"},
            {"path": "c", "hybrid_score": 0.3, "source_type": "context", "date": "2020-01-01"},
        ],
        top_k=10, today="2026-04-17",
    )
    _assert(out["status"] == "ok", f"expected ok, got {out}")
    order = [r["path"] for r in out["results"]]
    _assert(order == ["b", "a", "c"], f"expected hybrid ordering, got {order}")


def test_rerank_recency_boost() -> None:
    out = rerank.rerank(
        candidates=[
            {"path": "old", "hybrid_score": 0.9, "source_type": "context", "date": "2020-01-01"},
            {"path": "today", "hybrid_score": 0.8, "source_type": "context", "date": "2026-04-17"},
        ],
        top_k=10, today="2026-04-17",
    )
    # Same-day gets 1.15x boost; 0.8 * 1.15 = 0.92 > 0.9.
    _assert(out["results"][0]["path"] == "today", f"recency should promote today: {out['results']}")


def test_rerank_source_boost() -> None:
    out = rerank.rerank(
        candidates=[
            {"path": "ctx", "hybrid_score": 0.9, "source_type": "context", "date": "1999-01-01"},
            {"path": "transcript", "hybrid_score": 0.85, "source_type": "transcript", "date": "1999-01-01"},
        ],
        top_k=10, today="2026-04-17",
    )
    # transcript gets 1.10x; 0.85 * 1.10 = 0.935 > 0.9.
    _assert(out["results"][0]["path"] == "transcript",
            f"transcript boost should win: {out['results']}")


def test_rerank_invalid_input() -> None:
    out = rerank.rerank(candidates="nope")
    _assert(out["status"] == "error", f"string candidates must error, got {out}")


# ---------------------------------------------------------------------------
# Runner (no pytest dep)
# ---------------------------------------------------------------------------

def _discover_tests() -> list:
    return [
        (name, obj) for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]


def run() -> int:
    import inspect
    import tempfile

    failures: list[str] = []
    for name, fn in _discover_tests():
        try:
            sig = inspect.signature(fn)
            if "tmp_path" in sig.parameters:
                with tempfile.TemporaryDirectory() as td:
                    fn(Path(td))
            else:
                fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            print(f"  ERR   {name}: {type(exc).__name__}: {exc}")
    print()
    if failures:
        print(f"FAILED ({len(failures)})")
        return 1
    print(f"OK ({len(_discover_tests())} tests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

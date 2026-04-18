"""FTS5 + sqlite-vec access layer for the TARS hybrid retrieval index.

Phase 4 implementation — PRD §6.

Layout (one file, three virtual tables):
- ``fts_notes``  — FTS5 over Tier A + Tier B (title, tags, body).
- ``chunks``     — normal table, one row per Tier B chunk.
- ``vec_chunks`` — sqlite-vec virtual table, embedding per chunk. rowid matches
                   ``chunks.id`` one-to-one.
- ``meta``       — key/value schema + model bookkeeping.

The module does two jobs:
1. DB access (open / schema / upsert / search). No FastEmbed dependency here —
   the embedding call is injected by callers so tests can run stdlib-only.
2. Pure helpers — tier classification, body extraction, chunking, path hashing.

The embedding layer (FastEmbed load, model download) lives in the companion
build script ``scripts/build-search-index.py``; this module is also imported by
the MCP tools (``fts_search``, ``semantic_search``, ``rerank``).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence


INDEX_DB_RELATIVE = "_system/search.db"
INDEX_STATE_RELATIVE = "_system/search-index-state.json"
EMBED_DIM = 384  # bge-small-en-v1.5 / all-MiniLM-L6-v2 both 384-dim.
CHUNK_WORDS = 300  # ~400 tokens at 1.33 token/word.
CHUNK_OVERLAP_WORDS = 60  # ~80-token overlap.
SCHEMA_VERSION = "0.2.0-phase4"

TIER_A_PREFIXES = ("memory/",)
TIER_B_PREFIXES = ("journal/", "archive/transcripts/", "contexts/")
SOURCE_TYPE_BY_PREFIX = {
    "journal/": "journal",
    "archive/transcripts/": "transcript",
    "contexts/": "context",
    "memory/": "memory",
}


def index_path(vault: Path) -> Path:
    return Path(vault) / INDEX_DB_RELATIVE


def state_path(vault: Path) -> Path:
    return Path(vault) / INDEX_STATE_RELATIVE


# ---------------------------------------------------------------------------
# Tier + path helpers
# ---------------------------------------------------------------------------

def classify_tier(relative_path: str) -> str | None:
    """Return 'A', 'B', or None. ``relative_path`` uses forward slashes."""
    normalized = relative_path.lstrip("./")
    if any(normalized.startswith(p) for p in TIER_A_PREFIXES):
        return "A"
    if any(normalized.startswith(p) for p in TIER_B_PREFIXES):
        return "B"
    return None


def source_type_for(relative_path: str) -> str:
    normalized = relative_path.lstrip("./")
    for prefix, label in SOURCE_TYPE_BY_PREFIX.items():
        if normalized.startswith(prefix):
            return label
    return "other"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for buf in iter(lambda: fh.read(65536), b""):
            h.update(buf)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Markdown / frontmatter helpers (stdlib only)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_DATE_IN_PATH_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_raw, body). Frontmatter stays a raw YAML string."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def extract_title(path: Path, body: str) -> str:
    match = _TITLE_RE.search(body)
    if match:
        return match.group(1).strip()
    return path.stem


def extract_tags(frontmatter_raw: str) -> list[str]:
    """Best-effort tag extraction without PyYAML. Looks for ``tags:`` key."""
    tags: list[str] = []
    in_tags = False
    for raw_line in frontmatter_raw.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("tags:"):
            rest = line[len("tags:") :].strip()
            if rest.startswith("["):
                inner = rest.strip("[]")
                tags.extend(_split_inline(inner))
                in_tags = False
            else:
                in_tags = True
            continue
        if in_tags:
            if line.startswith("  -") or line.startswith("- "):
                tags.append(line.lstrip("- ").strip().strip('"').strip("'"))
            elif not line.startswith(" "):
                in_tags = False
    return [t for t in tags if t]


def _split_inline(inner: str) -> list[str]:
    return [t.strip().strip('"').strip("'") for t in inner.split(",") if t.strip()]


def extract_date(frontmatter_raw: str, relative_path: str) -> str | None:
    for line in frontmatter_raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("tars-date:"):
            value = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    match = _DATE_IN_PATH_RE.search(relative_path)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    index: int
    text: str


def chunk_body(
    body: str,
    chunk_words: int = CHUNK_WORDS,
    overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[Chunk]:
    """Split ``body`` into word-bounded chunks with overlap.

    Short bodies produce a single chunk. Zero-length bodies produce an empty
    list. The ~300-word / ~60-word-overlap defaults approximate the 400/80
    token budget specified in PRD §6.2 without a real tokenizer dependency.
    """
    if overlap_words >= chunk_words:
        raise ValueError("overlap_words must be smaller than chunk_words")
    words = body.split()
    if not words:
        return []
    if len(words) <= chunk_words:
        return [Chunk(index=0, text=" ".join(words))]
    stride = chunk_words - overlap_words
    chunks: list[Chunk] = []
    for start in range(0, len(words), stride):
        segment = words[start : start + chunk_words]
        if not segment:
            break
        chunks.append(Chunk(index=len(chunks), text=" ".join(segment)))
        if start + chunk_words >= len(words):
            break
    return chunks


# ---------------------------------------------------------------------------
# DB access
# ---------------------------------------------------------------------------

def load_sqlite_vec(conn: sqlite3.Connection) -> bool:
    """Attempt to load the sqlite-vec extension. Returns True on success.

    Callers that need vector search should treat False as "semantic layer
    unavailable — fall back to FTS-only".
    """
    try:
        import sqlite_vec  # type: ignore
    except Exception:
        return False
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception:
        return False
    return True


def open_index(db_path: Path, *, load_vec: bool = True) -> tuple[sqlite3.Connection, bool]:
    """Open (or create the parent dir of) the index DB. Returns (conn, vec_ok)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    vec_ok = load_sqlite_vec(conn) if load_vec else False
    return conn, vec_ok


def init_schema(conn: sqlite3.Connection, *, vec_enabled: bool) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_notes USING fts5(
            path, title, tags, body,
            tier UNINDEXED, source_type UNINDEXED, date UNINDEXED,
            tokenize = 'porter unicode61'
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            path          TEXT NOT NULL,
            chunk_index   INTEGER NOT NULL,
            text          TEXT NOT NULL,
            source_type   TEXT,
            date          TEXT,
            UNIQUE(path, chunk_index)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path);
        """
    )
    if vec_enabled:
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0("
            f"embedding float[{EMBED_DIM}])"
        )
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("schema_version", SCHEMA_VERSION),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
        ("vec_enabled", "1" if vec_enabled else "0"),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def delete_path(conn: sqlite3.Connection, relative_path: str, *, vec_enabled: bool) -> None:
    """Remove any existing rows for ``relative_path`` across all tables."""
    if vec_enabled:
        rows = conn.execute(
            "SELECT id FROM chunks WHERE path = ?", (relative_path,)
        ).fetchall()
        for row in rows:
            conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (row["id"],))
    conn.execute("DELETE FROM chunks WHERE path = ?", (relative_path,))
    conn.execute("DELETE FROM fts_notes WHERE path = ?", (relative_path,))


@dataclass
class NoteRecord:
    path: str          # vault-relative, forward slashes
    title: str
    tags: list[str] = field(default_factory=list)
    body: str = ""
    tier: str = "A"    # "A" or "B"
    source_type: str = "memory"
    date: str | None = None


def upsert_note_fts(conn: sqlite3.Connection, note: NoteRecord) -> None:
    conn.execute(
        "INSERT INTO fts_notes(path, title, tags, body, tier, source_type, date)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            note.path,
            note.title,
            " ".join(note.tags),
            note.body,
            note.tier,
            note.source_type,
            note.date or "",
        ),
    )


def upsert_chunks(
    conn: sqlite3.Connection,
    note: NoteRecord,
    chunks: Sequence[Chunk],
    embeddings: Sequence[Sequence[float]] | None,
    *,
    vec_enabled: bool,
) -> None:
    """Insert chunk rows and (if vec is enabled) their embeddings.

    ``embeddings`` may be None when the semantic layer is disabled — the chunk
    rows still land so FTS search can surface them.
    """
    if embeddings is not None and len(embeddings) != len(chunks):
        raise ValueError("embedding count must match chunk count")
    for idx, chunk in enumerate(chunks):
        cursor = conn.execute(
            "INSERT INTO chunks(path, chunk_index, text, source_type, date)"
            " VALUES (?, ?, ?, ?, ?)",
            (note.path, chunk.index, chunk.text, note.source_type, note.date or ""),
        )
        chunk_id = cursor.lastrowid
        if vec_enabled and embeddings is not None:
            conn.execute(
                "INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
                (chunk_id, _serialize_vector(embeddings[idx])),
            )


def _serialize_vector(vec: Sequence[float]) -> bytes:
    """sqlite-vec accepts a packed float32 BLOB for float[N] columns."""
    import struct

    return struct.pack(f"{len(vec)}f", *vec)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def fts_query(
    conn: sqlite3.Connection,
    query: str,
    *,
    tier: str | None = None,
    source_types: Iterable[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Keyword search. Returns rows ordered by bm25."""
    clauses = ["fts_notes MATCH ?"]
    params: list = [query]
    if tier:
        clauses.append("tier = ?")
        params.append(tier)
    if source_types:
        stypes = list(source_types)
        if stypes:
            placeholders = ",".join(["?"] * len(stypes))
            clauses.append(f"source_type IN ({placeholders})")
            params.extend(stypes)
    sql = (
        "SELECT path, title, source_type, date, tier,"
        " snippet(fts_notes, 3, '<<<', '>>>', '…', 12) AS snippet,"
        " bm25(fts_notes) AS score"
        f" FROM fts_notes WHERE {' AND '.join(clauses)}"
        " ORDER BY score LIMIT ?"
    )
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def semantic_query(
    conn: sqlite3.Connection,
    query_vector: Sequence[float],
    *,
    source_types: Iterable[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """Vector KNN against ``vec_chunks`` joined with ``chunks`` metadata.

    sqlite-vec's vec0 table exposes ``distance`` only when the WHERE clause
    contains ``embedding MATCH ?``. We over-fetch by a factor so the optional
    source-type filter still returns ``limit`` rows after filtering.
    """
    stypes = list(source_types) if source_types else []
    fetch_k = limit * 4 if stypes else limit
    match_sql = (
        "SELECT rowid, distance FROM vec_chunks"
        " WHERE embedding MATCH ? ORDER BY distance LIMIT ?"
    )
    matches = conn.execute(
        match_sql, (_serialize_vector(query_vector), fetch_k)
    ).fetchall()
    if not matches:
        return []
    results: list[dict] = []
    for row in matches:
        chunk = conn.execute(
            "SELECT path, chunk_index, text, source_type, date"
            " FROM chunks WHERE id = ?",
            (row["rowid"],),
        ).fetchone()
        if chunk is None:
            continue
        if stypes and chunk["source_type"] not in stypes:
            continue
        entry = dict(chunk)
        entry["distance"] = row["distance"]
        results.append(entry)
        if len(results) >= limit:
            break
    return results


# ---------------------------------------------------------------------------
# State file (incremental-build SHA map)
# ---------------------------------------------------------------------------

def load_state(path: Path) -> dict:
    if not path.is_file():
        return {"version": SCHEMA_VERSION, "files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": SCHEMA_VERSION, "files": {}}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")

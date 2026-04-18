#!/usr/bin/env python3
"""build-search-index — build the TARS hybrid retrieval index.

Tier A: SQLite FTS5 over ``memory/``.
Tier B: FTS5 + sqlite-vec over ``journal/``, ``archive/transcripts/``,
        ``contexts/``. Embeddings via FastEmbed (``BAAI/bge-small-en-v1.5``).

Writes ``_system/search.db`` and ``_system/search-index-state.json`` inside the
vault. Per PRD §6.4 the build is incremental — SHA-256 per file gates re-work.

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        report what would change, no writes
  --apply          write the index
  --json           emit machine-readable status
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.

Graceful degradation: if ``fastembed`` or ``sqlite-vec`` fails to import, the
script still builds the FTS5 layer. Semantic fallback signalled via meta.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

# The tars_vault package lives in mcp/tars-vault/src/tars_vault; add it so the
# script can reuse the shared helpers instead of duplicating chunking/schema.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "mcp" / "tars-vault" / "src"))

from tars_vault import search_index as si  # noqa: E402


DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
FALLBACK_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RUN_BUDGET_SECONDS = 600  # 10-minute cap per run (PRD §6.4 bounded).


class IndexError(Exception):
    """Raised for build errors that should translate to exit code 2."""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build-search-index")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="FastEmbed model name (default: BAAI/bge-small-en-v1.5)",
    )
    return parser


def verify_vault(vault: Path) -> tuple[bool, str]:
    if not vault.exists():
        return False, f"vault path does not exist: {vault}"
    if not vault.is_dir():
        return False, f"vault path is not a directory: {vault}"
    return True, ""


def verify_clean_worktree(vault: Path) -> tuple[bool, str]:
    """Migration-script contract (§26.15): refuse to run on a dirty worktree."""
    try:
        result = subprocess.run(
            ["git", "-C", str(vault), "status", "--porcelain"],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return True, ""  # Not a git repo — skip check rather than fail.
    if result.returncode != 0:
        return True, ""
    if result.stdout.strip():
        return False, "vault git worktree has uncommitted changes — refuse to run"
    return True, ""


# ---------------------------------------------------------------------------
# Vault walk
# ---------------------------------------------------------------------------

SKIP_DIR_NAMES = {".git", ".obsidian", "embedding-cache", "archive.bak"}


def walk_markdown(vault: Path) -> Iterable[Path]:
    for root, dirs, files in os.walk(vault):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
        for name in files:
            if name.endswith(".md"):
                yield Path(root) / name


# ---------------------------------------------------------------------------
# FastEmbed wrapper with graceful degradation
# ---------------------------------------------------------------------------

class Embedder:
    """Loads FastEmbed lazily. On import failure, ``available`` is False and
    callers must fall back to FTS-only mode."""

    def __init__(self, model: str, cache_dir: Path) -> None:
        self.model_name = model
        self.cache_dir = cache_dir
        self.available = False
        self._impl = None
        self._load()

    def _load(self) -> None:
        try:
            from fastembed import TextEmbedding  # type: ignore
        except Exception as exc:
            self._reason = f"fastembed import failed: {exc}"
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._impl = TextEmbedding(model_name=self.model_name, cache_dir=str(self.cache_dir))
        except Exception as exc:
            if self.model_name != FALLBACK_MODEL:
                try:
                    self._impl = TextEmbedding(model_name=FALLBACK_MODEL, cache_dir=str(self.cache_dir))
                    self.model_name = FALLBACK_MODEL
                except Exception as exc2:
                    self._reason = f"fastembed load failed: {exc2}"
                    return
            else:
                self._reason = f"fastembed load failed: {exc}"
                return
        self.available = True
        self._reason = ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.available or self._impl is None:
            raise IndexError(f"embedder unavailable: {self._reason}")
        return [list(map(float, v)) for v in self._impl.embed(texts)]

    @property
    def reason(self) -> str:
        return getattr(self, "_reason", "")


# ---------------------------------------------------------------------------
# Per-file indexing
# ---------------------------------------------------------------------------

def index_file(
    conn: sqlite3.Connection,
    vault: Path,
    file_path: Path,
    embedder: Embedder | None,
    *,
    vec_enabled: bool,
) -> dict:
    relative = file_path.relative_to(vault).as_posix()
    tier = si.classify_tier(relative)
    if tier is None:
        return {"path": relative, "status": "skipped"}
    text = file_path.read_text(encoding="utf-8", errors="replace")
    frontmatter_raw, body = si.split_frontmatter(text)
    title = si.extract_title(file_path, body)
    tags = si.extract_tags(frontmatter_raw)
    date = si.extract_date(frontmatter_raw, relative)
    source_type = si.source_type_for(relative)

    record = si.NoteRecord(
        path=relative,
        title=title,
        tags=tags,
        body=body,
        tier=tier,
        source_type=source_type,
        date=date,
    )

    si.delete_path(conn, relative, vec_enabled=vec_enabled)
    si.upsert_note_fts(conn, record)

    chunk_count = 0
    if tier == "B":
        chunks = si.chunk_body(body)
        chunk_count = len(chunks)
        embeddings = None
        if chunks and embedder is not None and embedder.available and vec_enabled:
            embeddings = embedder.embed([c.text for c in chunks])
        if chunks:
            si.upsert_chunks(conn, record, chunks, embeddings, vec_enabled=vec_enabled)
    return {"path": relative, "status": "indexed", "tier": tier, "chunks": chunk_count}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(vault: Path, *, apply_writes: bool, model: str) -> dict:
    db_path = si.index_path(vault)
    state_path = si.state_path(vault)
    state = si.load_state(state_path)
    files_state: dict = state.setdefault("files", {})

    candidates: list[tuple[Path, str]] = []
    for file_path in walk_markdown(vault):
        relative = file_path.relative_to(vault).as_posix()
        if si.classify_tier(relative) is None:
            continue
        sha = si.file_sha256(file_path)
        prior = files_state.get(relative, {})
        if prior.get("sha") == sha:
            continue
        candidates.append((file_path, sha))

    summary = {
        "vault": str(vault),
        "db_path": str(db_path),
        "state_path": str(state_path),
        "mode": "apply" if apply_writes else "dry-run",
        "candidate_files": len(candidates),
        "indexed": 0,
        "chunks": 0,
        "skipped_unchanged": len(files_state),
        "vec_enabled": False,
        "embedder_available": False,
        "embedder_reason": "",
        "model": model,
        "budget_exhausted": False,
    }

    if not apply_writes:
        summary["note"] = "dry-run — no writes. Use --apply to build."
        summary["candidates_sample"] = [p.relative_to(vault).as_posix() for p, _ in candidates[:20]]
        return summary

    conn, vec_enabled = si.open_index(db_path, load_vec=True)
    si.init_schema(conn, vec_enabled=vec_enabled)
    summary["vec_enabled"] = vec_enabled

    embedder = None
    if vec_enabled:
        embedder = Embedder(model, cache_dir=vault / "_system" / "embedding-cache")
        summary["embedder_available"] = embedder.available
        summary["embedder_reason"] = embedder.reason
        summary["model"] = embedder.model_name
    if not vec_enabled or (embedder is not None and not embedder.available):
        summary.setdefault("note", "semantic layer disabled — FTS-only index")

    started = time.monotonic()
    try:
        for file_path, sha in candidates:
            if time.monotonic() - started > RUN_BUDGET_SECONDS:
                summary["budget_exhausted"] = True
                break
            result = index_file(
                conn, vault, file_path, embedder,
                vec_enabled=vec_enabled and (embedder is None or embedder.available),
            )
            if result.get("status") == "indexed":
                summary["indexed"] += 1
                summary["chunks"] += result.get("chunks", 0)
                files_state[result["path"]] = {
                    "sha": sha,
                    "tier": result["tier"],
                    "chunks": result["chunks"],
                    "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
        conn.commit()
    finally:
        conn.close()
        si.save_state(state_path, state)

    return summary


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()

    ok, reason = verify_vault(vault)
    if not ok:
        print(f"error: {reason}", file=sys.stderr)
        return 3

    apply_writes = bool(args.apply) and not args.dry_run
    if apply_writes:
        clean_ok, clean_reason = verify_clean_worktree(vault)
        if not clean_ok:
            print(f"error: {clean_reason}", file=sys.stderr)
            return 3

    try:
        summary = run(vault, apply_writes=apply_writes, model=args.model)
    except IndexError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


def _handle_sigint(signum, frame):  # noqa: D401
    raise KeyboardInterrupt()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_sigint)
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

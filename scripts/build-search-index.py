#!/usr/bin/env python3
"""build-search-index — build the TARS hybrid retrieval index.

Tier A: SQLite FTS5 over ``memory/`` + ``journal/`` + structured notes.
Tier B: ``sqlite-vec`` vector index over long prose (journal, transcripts,
contexts). Embeddings via FastEmbed (BAAI/bge-small-en-v1.5).

Writes ``_system/search.db`` inside the vault. Phase 1a skeleton — the real
builder lands in Phase 4 per PRD §6.

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        report what would be indexed, no writes
  --apply          write the index (later phases)
  --json           emit machine-readable status
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state (e.g. dirty git tree).
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="build-search-index")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def verify_vault(vault: Path) -> tuple[bool, str]:
    if not vault.exists():
        return False, f"vault path does not exist: {vault}"
    if not vault.is_dir():
        return False, f"vault path is not a directory: {vault}"
    return True, ""


def init_db_schema(db_path: Path) -> None:
    """Create the empty FTS5 table. Phase 1a only — full schema in Phase 4."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
            INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', '0.1.0-skeleton');
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_notes USING fts5(
                path, title, tags, body,
                tokenize = 'porter unicode61'
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    ok, reason = verify_vault(vault)
    if not ok:
        print(f"error: {reason}", file=sys.stderr)
        return 3
    db_path = vault / "_system" / "search.db"
    payload = {
        "status": "skeleton",
        "vault": str(vault),
        "db_path": str(db_path),
        "mode": "dry-run" if args.dry_run or not args.apply else "apply",
    }
    if args.apply and not args.dry_run:
        init_db_schema(db_path)
        payload["note"] = "Initialized empty FTS5 schema (Phase 1a). Phase 4 adds semantic layer."
    else:
        payload["note"] = "Phase 1a skeleton: dry-run default. Use --apply to initialize the empty FTS5 schema."
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

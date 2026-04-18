"""append_note — Append content to an existing note, chunked at 40KB boundaries.

Resolves issue-obsidian-append-large-content by writing in 40_000-byte chunks
directly (no obsidian-cli dependency).

Arguments:
  vault:   required.
  file:    required. Vault-relative path.
  content: required. String to append.
  chunk_size: optional (default 40_000 bytes).

Returns:
  {status: ok, path, bytes_appended, chunks}
  {status: error, reason}
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from ..telemetry import append_event


DEFAULT_CHUNK = 40_000


def append_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    file_ = kwargs.get("file")
    content = kwargs.get("content")
    chunk_size = int(kwargs.get("chunk_size", DEFAULT_CHUNK))
    if chunk_size <= 0:
        return _common.error("chunk_size must be > 0")
    if not vault:
        return _common.error("missing 'vault'")
    if not file_:
        return _common.error("missing 'file'")
    if not isinstance(content, str):
        return _common.error("'content' must be a string")

    try:
        vault_p = _common.resolve_vault_path(vault)
        note_p = _common.resolve_note_path(vault_p, file_)
    except ValueError as exc:
        return _common.error(str(exc))

    if not note_p.is_file():
        return _common.error(f"note not found: {note_p.relative_to(vault_p)}")

    payload = content.encode("utf-8")
    chunks = 0
    with note_p.open("a", encoding="utf-8") as handle:
        for start in range(0, len(payload), chunk_size):
            end = min(start + chunk_size, len(payload))
            slice_str = payload[start:end].decode("utf-8", errors="replace")
            handle.write(slice_str)
            handle.flush()
            chunks += 1

    rel = str(note_p.relative_to(vault_p))
    append_event(
        Path(vault_p),
        {
            "event": "vault_write",
            "tool": "append_note",
            "file": rel,
            "bytes": len(payload),
            "chunks": chunks,
        },
    )
    return _common.ok(path=rel, bytes_appended=len(payload), chunks=chunks)

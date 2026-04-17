"""Tool namespace for tars-vault MCP server.

Each tool module exposes a single callable named identically to the module.
Phase 1a ships skeletons; later phases fill in the bodies per PRD §3.
"""
from . import (
    append_note,
    archive_note,
    classify_file,
    create_note,
    detect_near_duplicates,
    fts_search,
    move_note,
    read_note,
    refresh_integrations,
    rerank,
    resolve_capability,
    scan_secrets,
    search_by_tag,
    semantic_search,
    update_frontmatter,
    write_note_from_content,
)

__all__ = [
    "append_note",
    "archive_note",
    "classify_file",
    "create_note",
    "detect_near_duplicates",
    "fts_search",
    "move_note",
    "read_note",
    "refresh_integrations",
    "rerank",
    "resolve_capability",
    "scan_secrets",
    "search_by_tag",
    "semantic_search",
    "update_frontmatter",
    "write_note_from_content",
]

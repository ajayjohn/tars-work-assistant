"""write_note_from_content — Alias of create_note for the no-template path.

Resolves issue-obsidian-template-not-configured: skills don't need a registered
Obsidian template; pass the full frontmatter + body inline and write directly.
"""
from __future__ import annotations

from typing import Any

from .create_note import create_note


def write_note_from_content(**kwargs: Any) -> dict:
    return create_note(**kwargs)

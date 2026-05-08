"""write_note_from_content — Create a note from split args or full Markdown.

Resolves issue-obsidian-template-not-configured: skills don't need a registered
Obsidian template. Callers may pass frontmatter/body separately or a single
content blob with optional YAML frontmatter.
"""
from __future__ import annotations

from typing import Any

from .. import _common
from .create_note import create_note


def write_note_from_content(**kwargs: Any) -> dict:
    content = kwargs.get("content")
    has_split = kwargs.get("frontmatter") is not None or kwargs.get("body") is not None
    if content is not None and has_split:
        return _common.error("pass either content or frontmatter/body, not both")

    args = dict(kwargs)
    if content is not None:
        if not isinstance(content, str):
            return _common.error("'content' must be a string")
        frontmatter, body = _common.parse_full_content(content)
        args.pop("content", None)
        args["frontmatter"] = frontmatter
        args["body"] = body
    return create_note(**args)

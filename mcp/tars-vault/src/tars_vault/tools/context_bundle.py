"""context_bundle — Bounded context pack for a question or workflow."""
from __future__ import annotations

from typing import Any

from .. import _common
from .entity_timeline import entity_timeline
from .workspace_map import workspace_map


def context_bundle(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    query = str(kwargs.get("query") or "").strip()
    if not vault:
        return _common.error("missing 'vault'")
    if not query:
        return _common.error("missing 'query'")
    try:
        limit = max(1, min(int(kwargs.get("limit", 10)), 50))
    except (TypeError, ValueError):
        limit = 10

    wm = workspace_map(vault=vault, limit=min(limit, 20))
    timeline = entity_timeline(vault=vault, query=query, limit=limit)
    if wm.get("status") != "ok":
        return wm
    if timeline.get("status") != "ok":
        return timeline

    return _common.ok(
        query=query,
        generated_at=wm.get("generated_at"),
        workspace={
            "active_file_count": wm.get("active_file_count"),
            "context_gap_count": wm.get("context_gap_count"),
            "inbox": wm.get("inbox"),
            "tasks": wm.get("tasks"),
            "stale_active_initiatives": wm.get("initiatives", {}).get("stale_active", []),
        },
        timeline=timeline.get("entries", [])[:limit],
    )

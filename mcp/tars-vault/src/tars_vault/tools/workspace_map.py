"""workspace_map — Compact active-workspace map for routing and briefing."""
from __future__ import annotations

from typing import Any

from .. import _common
from ..activity_ledger import build_activity_ledger, write_activity_ledger


def workspace_map(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault'")
    try:
        limit = max(1, min(int(kwargs.get("limit", 20)), 100))
    except (TypeError, ValueError):
        limit = 20

    vault_p = _common.resolve_vault_path(vault)
    ledger = build_activity_ledger(vault_p)
    write_activity_ledger(vault_p, ledger)

    initiatives = dict(ledger.get("initiatives") or {})
    initiatives["active"] = initiatives.get("active", [])[:limit]
    initiatives["stale_active"] = initiatives.get("stale_active", [])[:limit]

    recent_journal = list(ledger.get("recent_journal") or [])[:limit]
    tasks = dict(ledger.get("tasks") or {})
    tasks["overdue"] = tasks.get("overdue", [])[:limit]

    return _common.ok(
        generated_at=ledger.get("generated_at"),
        active_file_count=ledger.get("active_file_count"),
        archive_file_count=ledger.get("archive_file_count"),
        by_root=ledger.get("by_root"),
        people=ledger.get("people"),
        decisions=ledger.get("decisions"),
        initiatives=initiatives,
        tasks=tasks,
        inbox=ledger.get("inbox"),
        recent_journal=recent_journal,
        context_gap_count=len(ledger.get("context_gaps") or []),
    )

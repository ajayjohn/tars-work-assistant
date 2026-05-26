"""context_gaps — Time-aware drift and low-input gap detector."""
from __future__ import annotations

from typing import Any

from .. import _common
from ..activity_ledger import build_activity_ledger, write_activity_ledger


def context_gaps(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault'")
    try:
        stale_days = max(1, int(kwargs.get("stale_days", 30)))
    except (TypeError, ValueError):
        stale_days = 30
    try:
        transcript_gap_days = max(1, int(kwargs.get("days_without_transcript", 30)))
    except (TypeError, ValueError):
        transcript_gap_days = 30

    vault_p = _common.resolve_vault_path(vault)
    ledger = build_activity_ledger(
        vault_p,
        stale_days=stale_days,
        transcript_gap_days=transcript_gap_days,
    )
    write_activity_ledger(vault_p, ledger)
    return _common.ok(
        generated_at=ledger.get("generated_at"),
        last=ledger.get("last"),
        gaps=ledger.get("context_gaps"),
        stale_active_initiatives=ledger.get("initiatives", {}).get("stale_active", []),
        overdue_tasks=ledger.get("tasks", {}).get("overdue", []),
        inbox=ledger.get("inbox"),
    )

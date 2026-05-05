#!/usr/bin/env python3
"""PreCompact hook.

Writes a session-summary stub to ``inbox/pending/claude-session-<ts>.md``
so the conversation surfaces in /maintain inbox for later review.

This is intentionally cheap: the hook only records *that* a session occurred
and what triggered it (compact event). A heavier "summarize the
conversation" pass over ``transcript_path`` lands later — /maintain inbox
can call /learn on the stub to upgrade it. The Claude binary does not run
in the background; this hook fires synchronously on the compact event and
must stay sub-second.

Recursion-guarded so the spawned /maintain run does not re-trigger.
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, vault_path, write_output


_TRIGGER = "pre-compact"


def _existing_stub_for_session(vault: Path, session_id: str, today: str) -> bool:
    """Return True if a stub with matching session_id and calendar day exists."""
    if not session_id:
        return False
    pending = vault / "inbox" / "pending"
    if not pending.is_dir():
        return False
    prefix = f"claude-session-{today}"
    for candidate in pending.iterdir():
        if not candidate.name.startswith(prefix) or not candidate.name.endswith(".md"):
            continue
        try:
            head = candidate.read_text(encoding="utf-8")[:600]
        except OSError:
            continue
        if f"tars-session-id: {session_id}" in head:
            return True
    return False


def _write_session_stub(vault: Path, event: dict) -> Path | None:
    """Write a minimal session-summary stub. Returns the path written or None."""
    try:
        ts = datetime.now().astimezone()
        slug = ts.strftime("%Y-%m-%d-%H%M%S")
        session_id = event.get("session_id") or ""
        today = ts.strftime("%Y-%m-%d")

        # Coalesce: skip if a stub for this (session_id, calendar_day) exists.
        if _existing_stub_for_session(vault, session_id, today):
            return None

        target = vault / "inbox" / "pending" / f"claude-session-{slug}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return None  # avoid clobbering an existing stub for the same second
        transcript_path = event.get("transcript_path") or ""
        body = (
            f"---\n"
            f"tags: [tars/inbox, tars/claude-session]\n"
            f"tars-source: claude-session\n"
            f"tars-trigger: {_TRIGGER}\n"
            f"tars-created: {ts.isoformat(timespec='seconds')}\n"
            f"tars-session-id: {session_id}\n"
            f"tars-transcript-path: {transcript_path}\n"
            f"tars-status: pending\n"
            f"---\n\n"
            f"# Claude session captured by {_TRIGGER}\n\n"
            f"This stub was written automatically when the session reached its compact "
            f"or end-of-session boundary. The original transcript lives at "
            f"`{transcript_path or '(unavailable)'}` and is preserved by Claude Code.\n\n"
            f"Run `/maintain inbox` to triage. Routing options for this entry type:\n"
            f"- decisions / commitments / questions surfaced during the session → "
            f"`/learn` and `/tasks` as appropriate.\n"
            f"- if the session was exploratory / no actionable signal, archive without "
            f"persisting.\n"
        )
        target.write_text(body, encoding="utf-8")
        return target
    except OSError:
        return None


def main() -> int:
    event = read_event()
    if in_recursion():
        return 0
    vault = vault_path()
    if not vault:
        write_output({})
        return 0
    _written = _write_session_stub(vault, event)
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"pre-compact hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

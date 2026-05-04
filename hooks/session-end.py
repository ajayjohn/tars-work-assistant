#!/usr/bin/env python3
"""SessionEnd hook.

Same shape as the PreCompact stub: write ``inbox/pending/claude-session-<ts>.md``
so /maintain inbox sees the session next time the user opens TARS.

Recursion-guarded.
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, vault_path, write_output


_TRIGGER = "session-end"


def _write_session_stub(vault: Path, event: dict) -> Path | None:
    try:
        ts = datetime.now().astimezone()
        slug = ts.strftime("%Y-%m-%d-%H%M%S")
        target = vault / "inbox" / "pending" / f"claude-session-{slug}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return None
        transcript_path = event.get("transcript_path") or ""
        session_id = event.get("session_id") or ""
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
            f"This stub was written when the session ended. The original transcript "
            f"lives at `{transcript_path or '(unavailable)'}` and is preserved by "
            f"Claude Code.\n\n"
            f"Run `/maintain inbox` to triage.\n"
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
        sys.stderr.write(f"session-end hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

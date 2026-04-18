#!/usr/bin/env python3
"""SessionStart hook. Observability-only — never exits non-zero.

Phase 1a skeleton. Reads the event, records the session-start timestamp if the
vault is available, and emits no additional context. Full banner logic (stale
housekeeping-state, cron health, alias head-load) lands in later phases per
PRD §3.2 and §3.5.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, vault_path, write_output


def main() -> int:
    _event = read_event()
    if in_recursion():
        return 0
    _vault = vault_path()
    # Phase 1a: skeleton only. Emit empty additionalContext so the harness sees
    # a valid response. Later phases populate banners + registry refresh.
    write_output({"hookSpecificOutput": {"additionalContext": ""}})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"session-start hook error: {exc}\n")
        rc = 0  # never block the session
    sys.exit(rc)

#!/usr/bin/env python3
"""PreCompact hook. Phase 1a skeleton.

Later phases spawn a detached subprocess that runs a Haiku pass over the
conversation and writes `inbox/pending/claude-session-YYYY-MM-DD-HHMMSS.md`.
The skeleton only guards against recursion and returns cleanly.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, write_output


def main() -> int:
    _event = read_event()
    if in_recursion():
        return 0
    # Detached-subprocess spawn lands in Phase 5 per PRD §5 and §26.5.
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"pre-compact hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

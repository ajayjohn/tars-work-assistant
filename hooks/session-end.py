#!/usr/bin/env python3
"""SessionEnd hook. Phase 1a skeleton.

Same extraction pattern as pre-compact; routed to
`inbox/pending/claude-session-*.md`. Recursion-guarded.
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
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"session-end hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

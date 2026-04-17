#!/usr/bin/env python3
"""PostToolUse hook. Phase 1a skeleton.

Fire-and-forget. On successful vault mutation, later phases append a row to
`_system/changelog/YYYY-MM-DD.md`. On failure, they dedupe into
`_system/backlog/issues/`. The skeleton only validates the event shape.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, write_output


def main() -> int:
    event = read_event()
    _tool_name = event.get("tool_name")
    _tool_response = event.get("tool_response")
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"post-tool-use hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

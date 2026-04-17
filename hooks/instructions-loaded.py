#!/usr/bin/env python3
"""InstructionsLoaded hook. Phase 1a skeleton.

Later phases append a `skill_loaded` row to `_system/telemetry/YYYY-MM-DD.jsonl`.
Observability-only — never exits non-zero.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, write_output


def main() -> int:
    _event = read_event()
    # Telemetry append lands Phase 5 per PRD §26.11.
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"instructions-loaded hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

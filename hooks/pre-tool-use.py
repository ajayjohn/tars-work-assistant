#!/usr/bin/env python3
"""PreToolUse hook. Phase 1a skeleton.

May exit 2 to deny a tool call. PRD §3.2 enumerates the rules the final
implementation must enforce; this skeleton only establishes the event-loop
shape so later phases can plug logic in without restructuring.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, write_output


def main() -> int:
    event = read_event()
    tool_name = str(event.get("tool_name") or "")
    tool_input = event.get("tool_input") or {}
    # Phase 1a: accept everything. Later phases check:
    #   * obsidian create without path= / name= (exit 2)
    #   * non-tars- prefix on managed note (exit 2)
    #   * payload > 40KB (warn + suggest MCP chunked variant)
    _ = (tool_name, tool_input)
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"pre-tool-use hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

#!/usr/bin/env python3
"""discover-mcp-tools — enumerate installed MCP servers and classify their tools
into TARS capability categories per the taxonomy in PRD §3.5.

Phase 1a skeleton. Full behaviour (parse Claude Code MCP introspection context,
classify via scripts/capability-classifier.py, write ``_system/tools-registry.yaml``)
lands in Phase 1b/2.

Contract per PRD §26.15:
  --vault <path>   required (except --dry-run without --write)
  --dry-run        print proposed output, no writes
  --apply          write the registry (default off until Phase 1b wires it)
  --json           emit machine-readable output
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.
"""
import argparse
import json
import os
import sys
from datetime import datetime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="discover-mcp-tools")
    parser.add_argument("--vault", required=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    skeleton_payload = {
        "status": "skeleton",
        "discovered_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mcp_servers": {},
        "note": "Phase 1a skeleton — Phase 1b wires Claude Code MCP introspection + classifier.",
    }
    if args.json:
        print(json.dumps(skeleton_payload, indent=2))
    else:
        print("discover-mcp-tools: Phase 1a skeleton. No writes performed.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

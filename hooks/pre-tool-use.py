#!/usr/bin/env python3
"""PreToolUse hook.

Phase 1 (v3.2): refuse `mcp__tars_vault__*` mutations when install.yaml
disagrees with the current working directory. Prevents silent writes into a
moved or duplicated vault. Other PreToolUse rules (40KB cap, tars- prefix,
wikilink scanning) land in later phases per the v3.2 plan.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, resolve_vault, write_output


_MUTATION_TOOLS = frozenset(
    {
        "mcp__tars_vault__create_note",
        "mcp__tars_vault__append_note",
        "mcp__tars_vault__write_note_from_content",
        "mcp__tars_vault__update_frontmatter",
        "mcp__tars_vault__archive_note",
        "mcp__tars_vault__move_note",
    }
)


def _deny(reason: str) -> None:
    write_output(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    )


def main() -> int:
    event = read_event()
    tool_name = str(event.get("tool_name") or "")
    if tool_name not in _MUTATION_TOOLS:
        write_output({})
        return 0
    _vault, status = resolve_vault()
    if status.get("mismatch"):
        install = status.get("install") or {}
        stored = install.get("vault_path") or "(unset)"
        _deny(
            "Refusing vault write: this folder does not match the vault recorded in "
            f"_system/install.yaml (vault_path={stored}). Run /welcome --relocate to "
            "update the install record before writing."
        )
        return 0
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"pre-tool-use hook error: {exc}\n")
        # On error, fall through (write nothing) so the user is not blocked.
        sys.stdout.write(json.dumps({}))
        rc = 0
    sys.exit(rc)

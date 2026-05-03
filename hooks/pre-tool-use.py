#!/usr/bin/env python3
"""PreToolUse hook.

v3.2 enforces two safety rules at the hook layer:

  1. Refuse ``mcp__tars_vault__*`` mutations when ``_system/install.yaml``
     disagrees with the current working directory (Phase 1).

  2. Refuse mutations whose content payload contains wikilinks with smart
     quotes or characters Obsidian forbids in filenames (Phase 2). The
     in-house MCP server enforces the same rule for defense-in-depth, but
     the hook catches the same issue before the MCP server ever sees the
     payload — useful when the user runs Bash-driven writes.

Other PreToolUse rules (40KB cap, ``tars-`` prefix enforcement) land in
later phases.
"""
import json
import re
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


# Mirrors the canonical sets in tars_vault/sanitize.py. Duplicated here so
# the hook stays stdlib-only without importing the MCP package (which adds
# fastembed/sqlite-vec runtime requirements the hook should not depend on).
_SMART_QUOTES = "‘’‚‛“”„‟′″–—…"
_FORBIDDEN_FN_CHARS = '\\/:*?"<>|'  # excluding # and | which separate heading/display
_WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")


def _scan_bad_wikilinks(text: str) -> list[str]:
    """Return human-readable findings for any offending wikilink in ``text``."""
    if not isinstance(text, str) or not text:
        return []
    out: list[str] = []
    for match in _WIKILINK_RE.finditer(text):
        raw = match.group(1)
        body = raw.split("|", 1)[0]
        body = body.split("#", 1)[0].strip()
        if not body:
            out.append(f"[[{raw}]] has empty target")
            continue
        if any(ch in _SMART_QUOTES for ch in raw):
            out.append(f"[[{raw}]] contains smart quotes — normalize to straight ASCII")
            continue
        if any(ch in _FORBIDDEN_FN_CHARS for ch in body):
            out.append(
                f"[[{raw}]] contains characters Obsidian forbids in filenames "
                '(\\ / : * ? " < > |)'
            )
    return out


def _content_fields(tool_name: str, tool_input: dict) -> list[str]:
    """Return the strings from a tool input that should be wikilink-scanned."""
    fields: list[str] = []
    if tool_name == "mcp__tars_vault__append_note":
        v = tool_input.get("content")
        if isinstance(v, str):
            fields.append(v)
    elif tool_name in (
        "mcp__tars_vault__create_note",
        "mcp__tars_vault__write_note_from_content",
    ):
        v = tool_input.get("body")
        if isinstance(v, str):
            fields.append(v)
    elif tool_name == "mcp__tars_vault__update_frontmatter":
        # Frontmatter values rarely contain wikilinks but treat string values defensively.
        updates = tool_input.get("updates")
        if isinstance(updates, dict):
            for v in updates.values():
                if isinstance(v, str):
                    fields.append(v)
    return fields


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
    tool_input = event.get("tool_input") or {}
    if tool_name not in _MUTATION_TOOLS:
        write_output({})
        return 0

    # Rule 1: install.yaml mismatch.
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

    # Rule 2: bad wikilinks in content payload.
    findings: list[str] = []
    for chunk in _content_fields(tool_name, tool_input if isinstance(tool_input, dict) else {}):
        findings.extend(_scan_bad_wikilinks(chunk))
    if findings:
        _deny(
            "Refusing vault write: wikilink validation failed. "
            "Use mcp__tars_vault__format_wikilink to form links. Findings: "
            + "; ".join(findings)
        )
        return 0

    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"pre-tool-use hook error: {exc}\n")
        sys.stdout.write(json.dumps({}))
        rc = 0
    sys.exit(rc)

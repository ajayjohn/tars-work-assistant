#!/usr/bin/env python3
"""PreToolUse hook.

v3.2 enforces four safety rules at the hook layer (defense-in-depth: the
in-house MCP server runs the same checks server-side, but the hook catches
issues before the MCP ever sees the payload — including for Bash-driven
writes that bypass the MCP):

  1. Refuse ``mcp__tars_vault__*`` mutations when ``_system/install.yaml``
     disagrees with the current working directory (Phase 1).

  2. Refuse mutations whose content payload contains wikilinks with smart
     quotes or characters Obsidian forbids in filenames (Phase 2).

  3. Refuse `create_note` / `write_note_from_content` whose body exceeds
     40,000 bytes — point the caller at `append_note`, which chunks
     server-side (Phase 4).

  4. Refuse `create_note` / `update_frontmatter` whose frontmatter (or
     `updates` map) contains keys that are neither ``tars-`` prefixed nor
     in the reserved set (`tags`, `aliases`), unless the caller passes
     `allow_user_properties=true` (Phase 4).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import (
    enabled_extension_policies,
    extension_loaded,
    last_loaded_skill,
    provider_tool_matches,
    read_event,
    resolve_vault,
    write_output,
)


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


_NON_PREFIX_RESERVED = frozenset({"tags", "aliases"})
_BODY_BYTE_LIMIT = 40_000


def _check_payload_size(tool_name: str, tool_input: dict) -> str:
    """Return a deny reason if a non-chunking write tool exceeds 40KB.

    `append_note` is the chunking variant — it is *meant* to take large
    payloads — so we only guard `create_note` / `write_note_from_content`.
    """
    if tool_name not in (
        "mcp__tars_vault__create_note",
        "mcp__tars_vault__write_note_from_content",
    ):
        return ""
    body = tool_input.get("body")
    if not isinstance(body, str):
        return ""
    n = len(body.encode("utf-8"))
    if n > _BODY_BYTE_LIMIT:
        return (
            f"Refusing workspace write: body is {n:,} bytes which exceeds the "
            f"{_BODY_BYTE_LIMIT:,}-byte cap on {tool_name.split('__')[-1]}. "
            "Use mcp__tars_vault__append_note (chunked) for large content, or "
            "split the write across multiple notes."
        )
    return ""


def _check_prefix(tool_name: str, tool_input: dict) -> str:
    """Return a deny reason if frontmatter/updates contain non-tars keys.

    Allows: tars-* keys; tags / aliases; anything when allow_user_properties=true.
    """
    if tool_name == "mcp__tars_vault__create_note":
        fm = tool_input.get("frontmatter") or {}
        if not isinstance(fm, dict):
            return ""
        if tool_input.get("allow_user_properties"):
            return ""
        bad = [
            k for k in fm.keys()
            if not k.startswith("tars-") and k not in _NON_PREFIX_RESERVED
        ]
        if bad:
            return (
                f"Refusing workspace write: frontmatter keys "
                f"{', '.join(repr(k) for k in bad)} are not tars-prefixed and "
                "not reserved (tags, aliases). Pass allow_user_properties=true "
                "to permit user-owned keys."
            )
        return ""
    if tool_name == "mcp__tars_vault__update_frontmatter":
        updates = tool_input.get("updates") or {}
        if not isinstance(updates, dict):
            return ""
        if tool_input.get("allow_user_properties"):
            return ""
        bad = [
            k for k in updates.keys()
            if not k.startswith("tars-") and k not in _NON_PREFIX_RESERVED
        ]
        if bad:
            return (
                f"Refusing frontmatter update: keys "
                f"{', '.join(repr(k) for k in bad)} are not tars-prefixed and "
                "not reserved (tags, aliases). Pass allow_user_properties=true "
                "to permit user-owned keys."
            )
    return ""


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


def _under_claude_home(path: Path) -> bool:
    try:
        return path.expanduser().resolve().is_relative_to((Path.home() / ".claude").resolve())
    except Exception:
        return False


def _claude_home_write_reason(vault: Path | None, tool_input: dict) -> str:
    """Block fresh workspace writes under ~/.claude unless explicitly installed."""
    candidate = vault
    raw = tool_input.get("vault") if isinstance(tool_input, dict) else None
    if raw and isinstance(raw, str):
        candidate = Path(raw).expanduser()
    if candidate is None or not _under_claude_home(candidate):
        return ""
    install = candidate / "_system" / "install.yaml"
    if install.is_file():
        return ""
    return (
        "Refusing workspace write: the active workspace resolves under ~/.claude, "
        "which is usually application state rather than a transparent TARS workspace. "
        "Set TARS_VAULT_PATH to a folder such as ~/Documents/TARS Workspace and rerun "
        "/welcome, or run scripts/doctor.py to inspect the path."
    )


def main() -> int:
    event = read_event()
    tool_name = str(event.get("tool_name") or "")
    tool_input = event.get("tool_input") or {}
    _vault, status = resolve_vault()
    session_id = str(event.get("session_id", ""))
    if tool_name.startswith("mcp__") and not tool_name.startswith("mcp__tars_vault__") and _vault is not None:
        active_skill = last_loaded_skill(_vault, session_id)
        for policy in enabled_extension_policies(_vault):
            if policy.get("enforcement") not in {"required", "fail_closed"}:
                continue
            applies_to = policy.get("applies_to_skills") or []
            if applies_to and active_skill and active_skill not in applies_to:
                continue
            if not any(provider_tool_matches(str(pattern), tool_name) for pattern in policy.get("provider_tools", [])):
                continue
            extension_id = str(policy.get("extension_id") or "")
            if extension_id and not extension_loaded(_vault, session_id, extension_id):
                contract = policy.get("tool_contract") or "the extension instructions"
                _deny(
                    "Refusing direct provider MCP call because enabled TARS extension "
                    f"{extension_id} governs {tool_name} with {policy.get('enforcement')} "
                    "enforcement. Call mcp__tars_vault__resolve_extension and "
                    f"mcp__tars_vault__read_extension first, then follow {contract}."
                )
                return 0

    if tool_name not in _MUTATION_TOOLS:
        write_output({})
        return 0

    # Rule 1: install.yaml mismatch.
    ti = tool_input if isinstance(tool_input, dict) else {}
    claude_home_reason = _claude_home_write_reason(_vault, ti)
    if claude_home_reason:
        _deny(claude_home_reason)
        return 0

    if status.get("mismatch"):
        install = status.get("install") or {}
        stored = install.get("workspace_path") or install.get("vault_path") or "(unset)"
        _deny(
            "Refusing workspace write: this folder does not match the workspace recorded in "
            f"_system/install.yaml (workspace_path={stored}). Run /welcome --relocate to "
            "update the install record before writing."
        )
        return 0

    # Rule 2: bad wikilinks in content payload.
    findings: list[str] = []
    for chunk in _content_fields(tool_name, ti):
        findings.extend(_scan_bad_wikilinks(chunk))
    if findings:
        _deny(
            "Refusing workspace write: wikilink validation failed. "
            "Use mcp__tars_vault__format_wikilink to form links. Findings: "
            + "; ".join(findings)
        )
        return 0

    # Rule 3: 40KB body cap on non-chunking write tools.
    size_reason = _check_payload_size(tool_name, ti)
    if size_reason:
        _deny(size_reason)
        return 0

    # Rule 4: tars- prefix enforcement on frontmatter / updates.
    prefix_reason = _check_prefix(tool_name, ti)
    if prefix_reason:
        _deny(prefix_reason)
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

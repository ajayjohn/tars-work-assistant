#!/usr/bin/env python3
"""PostToolUse hook.

Fire-and-forget. On successful vault-mutating MCP tool use, emit a
``vault_write`` telemetry event (§26.11) so `/lint` and `_views/skill-activity.base`
have something to work with. Changelog append + backlog dedupe for failures still
lands in a future phase; for now this hook captures the signal.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, write_output, vault_path, in_recursion, append_telemetry, record_extension_loaded


# MCP tools that mutate the vault — their success events warrant telemetry.
MUTATING_TOOLS = {
    "mcp__tars_vault__create_note",
    "mcp__tars_vault__append_note",
    "mcp__tars_vault__write_note_from_content",
    "mcp__tars_vault__update_frontmatter",
    "mcp__tars_vault__move_note",
    "mcp__tars_vault__archive_note",
}


def _extract_file(tool_input: dict) -> str | None:
    for key in ("file", "path", "name", "src", "dst"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _is_error_response(tool_response: object) -> bool:
    if isinstance(tool_response, dict):
        return bool(tool_response.get("isError") or tool_response.get("error"))
    if isinstance(tool_response, str):
        return "error" in tool_response.lower() and "status" in tool_response.lower()
    return False


def main() -> int:
    event = read_event()
    if in_recursion():
        write_output({})
        return 0
    vault = vault_path()
    if vault is None:
        write_output({})
        return 0

    tool_name = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    tool_response = event.get("tool_response") or {}
    # Mark extension instructions as loaded once read_extension succeeds. The
    # provider bypass guard uses this as its session-scoped acknowledgement.
    if tool_name == "mcp__tars_vault__read_extension":
        extension_id = ""
        if isinstance(tool_input, dict):
            extension_id = str(tool_input.get("extension_id") or tool_input.get("id") or "")
        if extension_id and not _is_error_response(tool_response):
            record_extension_loaded(vault, str(event.get("session_id", "")), extension_id)
        write_output({})
        return 0

    if tool_name not in MUTATING_TOOLS:
        write_output({})
        return 0

    # Respect both string + object response shapes. Treat missing error as success.
    if _is_error_response(tool_response):
        write_output({})
        return 0

    append_telemetry(
        vault,
        {
            "event": "vault_write",
            "session_id": event.get("session_id", ""),
            "tool": tool_name,
            "file": _extract_file(tool_input) or "",
        },
    )
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"post-tool-use hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

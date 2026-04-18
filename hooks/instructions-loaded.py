#!/usr/bin/env python3
"""InstructionsLoaded hook.

Emits a ``skill_loaded`` telemetry event when a TARS skill's instructions are
loaded into the conversation. Observability-only — never exits non-zero.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import read_event, write_output, vault_path, in_recursion, append_telemetry


def _skill_from_event(event: dict) -> str | None:
    # Claude Code's InstructionsLoaded event surfaces the skill name in a few
    # possible shapes depending on version. Check the likely keys; return None
    # if we can't tell — silent no-op in that case.
    for key in ("skill", "skill_name", "name"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value.lstrip("/")
    instructions = event.get("instructions") or {}
    if isinstance(instructions, dict):
        for key in ("skill", "name"):
            value = instructions.get(key)
            if isinstance(value, str) and value:
                return value.lstrip("/")
    return None


def main() -> int:
    event = read_event()
    if in_recursion():
        write_output({})
        return 0
    vault = vault_path()
    skill = _skill_from_event(event)
    if vault is not None and skill:
        append_telemetry(
            vault,
            {
                "event": "skill_loaded",
                "session_id": event.get("session_id", ""),
                "skill": skill,
            },
        )
    write_output({})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"instructions-loaded hook error: {exc}\n")
        rc = 0
    sys.exit(rc)

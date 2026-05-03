#!/usr/bin/env python3
"""SessionStart hook. Observability-only — never exits non-zero.

Phase 1 (v3.2): adds vault-path validation. If install.yaml.vault_path
disagrees with the current working directory, surface a loud warning via
``additionalContext`` so the user notices before any write happens.

Banner content beyond the mismatch warning, cron-job re-registration, and
integrations-registry refresh are still pending later phases.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from _common import in_recursion, read_event, resolve_vault, write_output


def _build_context(status: dict) -> str:
    if status.get("mismatch"):
        install = status.get("install") or {}
        stored = install.get("vault_path") or "(unset)"
        return (
            "TARS install warning: this folder does not match the vault recorded in "
            "_system/install.yaml.\n"
            f"  Recorded vault_path: {stored}\n"
            "  If you moved or copied the vault, run /welcome --relocate to update "
            "the install record. Until then, writes are discouraged from this folder."
        )
    if status.get("source") == "cwd-config":
        return (
            "TARS notice: this vault has no _system/install.yaml. Run /welcome to "
            "create one — until then, vault-move detection is disabled."
        )
    return ""


def main() -> int:
    _event = read_event()
    if in_recursion():
        return 0
    _vault, status = resolve_vault()
    write_output({"hookSpecificOutput": {"additionalContext": _build_context(status)}})
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"session-start hook error: {exc}\n")
        rc = 0  # never block the session
    sys.exit(rc)

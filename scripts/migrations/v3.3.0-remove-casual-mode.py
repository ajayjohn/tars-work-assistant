"""Migration v3.3.0-remove-casual-mode

Removes the `mode:` field from _system/install.yaml for all existing vaults.

Rationale: v3.2.0 introduced a casual/standard bifurcation controlled by a
`mode:` field in install.yaml. v3.3.0 removes this distinction in favour of
uniform graceful degradation — TARS works out of the box for all users and
gains capability as integrations are connected. The `mode` field is now
obsolete and would be ignored silently; removing it prevents future confusion.

Contract: run(vault, dry_run) as required by scripts/run-migrations.py.
"""

from pathlib import Path
import re


_INSTALL_PATH = "_system/install.yaml"
_MODE_RE = re.compile(
    r"^# Engagement mode\..*?\nmode: (?:standard|casual)\n",
    re.MULTILINE | re.DOTALL,
)
_MODE_LINE_RE = re.compile(r"^mode: (?:standard|casual)\n", re.MULTILINE)


def run(vault: Path, dry_run: bool = True) -> dict:
    """Remove the `mode:` field (and its comment block) from _system/install.yaml.

    Returns a result dict compatible with run-migrations.py expectations:
      {"status": "ok"|"skip"|"error", "changes": [...], "message": str}
    """
    target = vault / _INSTALL_PATH
    if not target.is_file():
        return {
            "status": "skip",
            "changes": [],
            "message": f"{_INSTALL_PATH} not found — vault not yet onboarded.",
        }

    try:
        original = target.read_text(encoding="utf-8")
    except OSError as exc:
        return {"status": "error", "changes": [], "message": f"Read failed: {exc}"}

    # Try stripping the full comment block + mode line first.
    updated = _MODE_RE.sub("", original)
    if updated == original:
        # Comment block not present; try stripping the bare `mode:` line only.
        updated = _MODE_LINE_RE.sub("", original)

    if updated == original:
        return {
            "status": "skip",
            "changes": [],
            "message": f"{_INSTALL_PATH} has no `mode:` field — nothing to do.",
        }

    changes = [
        {
            "file": str(target.relative_to(vault)),
            "action": "remove_field",
            "field": "mode",
            "before": _extract_mode_value(original),
        }
    ]

    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "changes": changes,
            "message": "Would remove `mode:` field from _system/install.yaml.",
        }

    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return {"status": "error", "changes": [], "message": f"Write failed: {exc}"}

    return {
        "status": "ok",
        "dry_run": False,
        "changes": changes,
        "message": "Removed `mode:` field from _system/install.yaml.",
    }


def _extract_mode_value(text: str) -> str:
    m = _MODE_LINE_RE.search(text)
    if m:
        return m.group(0).strip()
    return "unknown"

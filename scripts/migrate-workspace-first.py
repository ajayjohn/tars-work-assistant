#!/usr/bin/env python3
"""Backfill workspace-first install fields for existing TARS workspaces.

This is intentionally standalone rather than version-gated by
scripts/run-migrations.py. Existing users may already be on the same plugin
version that introduced workspace-first language, so the migration must be safe
to run explicitly at any time.

Behavior:
  * Preserves existing memory, journal, schedules, integrations, and views.
  * Reads _system/install.yaml if present.
  * Adds workspace_type, workspace_path, obsidian_enabled, and
    obsidian_vault_path when missing.
  * Keeps vault_path as a backward-compatible alias for workspace_path.
  * Defaults legacy installs to obsidian mode so existing users do not lose
    their current browsing/view behavior. Users can switch later with
    /welcome --disable-obsidian.
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


INSTALL_REL = Path("_system/install.yaml")
PLUGIN_JSON = Path(__file__).resolve().parents[1] / ".claude-plugin" / "plugin.json"


def _parse_flat_yaml(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        key = match.group(1)
        value = match.group(2).strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        out[key] = value
    return out


def _load_plugin_version() -> str:
    try:
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        return str(data.get("version") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    text = str(value)
    if text == "":
        return '""'
    if re.search(r"[:#\n]|^\s|\s$", text):
        return json.dumps(text)
    return text


def _upsert(text: str, key: str, value: Any) -> tuple[str, bool]:
    rendered = f"{key}: {_yaml_scalar(value)}"
    pattern = re.compile(rf"^{re.escape(key)}\s*:.*$", re.MULTILINE)
    if pattern.search(text):
        updated = pattern.sub(rendered, text)
        return updated, updated != text
    if text and not text.endswith("\n"):
        text += "\n"
    return text + rendered + "\n", True


def _matches(existing: str | None, desired: Any) -> bool:
    if existing is None:
        return False
    if isinstance(desired, bool):
        return existing.lower() == ("true" if desired else "false")
    return existing == str(desired)


def _default_install_text() -> str:
    return (
        "# TARS install state - workspace-specific configuration written by migration.\n"
        "# Edit via /welcome or /lint --actions.\n"
    )


def migrate(vault: Path, apply: bool) -> dict[str, Any]:
    vault = vault.expanduser().resolve()
    install_path = vault / INSTALL_REL
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    changes: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    if install_path.exists():
        try:
            original = install_path.read_text(encoding="utf-8")
        except OSError as exc:
            return {
                "status": "error",
                "dry_run": not apply,
                "changes": [],
                "errors": [{"file": str(INSTALL_REL), "error": str(exc)}],
            }
    else:
        original = _default_install_text()
        changes.append({
            "file": str(INSTALL_REL),
            "action": "create",
            "detail": "Create install record for legacy workspace.",
        })

    parsed = _parse_flat_yaml(original)
    legacy_path = parsed.get("vault_path") or str(vault)
    workspace_path = parsed.get("workspace_path") or legacy_path

    if "obsidian_enabled" in parsed:
        obsidian_enabled = parsed["obsidian_enabled"].lower() == "true"
    else:
        obsidian_enabled = True

    workspace_type = parsed.get("workspace_type") or ("obsidian" if obsidian_enabled else "headless")
    obsidian_vault_path = parsed.get("obsidian_vault_path") or (
        workspace_path if obsidian_enabled else ""
    )

    desired: dict[str, Any] = {
        "workspace_type": workspace_type,
        "workspace_path": workspace_path,
        "vault_path": workspace_path,
        "obsidian_enabled": obsidian_enabled,
        "obsidian_vault_path": obsidian_vault_path,
        "installation_id": parsed.get("installation_id") or str(uuid.uuid4()),
        "persona": parsed.get("persona") or "",
        "plugin_version": parsed.get("plugin_version") or _load_plugin_version(),
        "created": parsed.get("created") or now,
        "last_session_at": parsed.get("last_session_at") or now,
        "scheduler_type": parsed.get("scheduler_type") or "",
    }

    updated = original
    for key, value in desired.items():
        before = _parse_flat_yaml(updated).get(key)
        if _matches(before, value):
            continue
        updated, changed = _upsert(updated, key, value)
        if changed:
            changes.append({
                "file": str(INSTALL_REL),
                "action": "upsert",
                "detail": f"{key}: {before or '(missing)'} -> {value}",
            })

    if apply and updated != original:
        try:
            install_path.parent.mkdir(parents=True, exist_ok=True)
            install_path.write_text(updated, encoding="utf-8")
        except OSError as exc:
            errors.append({"file": str(INSTALL_REL), "error": str(exc)})

    return {
        "status": "error" if errors else "ok",
        "dry_run": not apply,
        "workspace_path": workspace_path,
        "workspace_type": workspace_type,
        "obsidian_enabled": obsidian_enabled,
        "changes": changes,
        "errors": errors,
        "skipped": 0 if changes else 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill workspace-first fields in _system/install.yaml.")
    parser.add_argument("--vault", required=True, help="Path to the existing TARS workspace or vault.")
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry run.")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print JSON output.")
    args = parser.parse_args()

    result = migrate(Path(args.vault), apply=args.apply)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        mode = "apply" if args.apply else "dry run"
        print(f"Workspace-first migration ({mode})")
        print(f"Status: {result['status']}")
        print(f"Workspace: {result.get('workspace_path', '')}")
        print(f"Mode: {result.get('workspace_type', '')}")
        print(f"Obsidian enabled: {result.get('obsidian_enabled', False)}")
        if result["changes"]:
            print("Changes:")
            for change in result["changes"]:
                print(f"  - {change['detail']}")
        else:
            print("No changes needed.")
        for error in result["errors"]:
            print(f"ERROR {error['file']}: {error['error']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

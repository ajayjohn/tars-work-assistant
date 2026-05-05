#!/usr/bin/env python3
"""TARS Migration Runner.

Discovers and applies pending schema / vault-structure migrations.  Each
migration is a self-contained Python script in scripts/migrations/ that
follows the contract below.  The runner compares the vault's recorded
plugin_version (in _system/housekeeping-state.yaml) against the plugin's
current version (in .claude-plugin/plugin.json) and runs all migrations
whose version tag falls in the gap.

Migration contract
------------------
Each script in scripts/migrations/ must be named:

    <version>-<slug>.py          e.g. v3.2.0-add-tars-category.py

It must expose a top-level function:

    def run(vault: Path, dry_run: bool) -> dict:
        ...
        return {
            "migration": "<version>-<slug>",
            "dry_run": bool,
            "changes": [{"file": str, "action": str, "detail": str}, ...],
            "errors":  [{"file": str, "error": str}, ...],
            "skipped": int,   # already-correct notes skipped
        }

Usage
-----
    python3 scripts/run-migrations.py --vault /path/to/vault --list
    python3 scripts/run-migrations.py --vault /path/to/vault --dry-run
    python3 scripts/run-migrations.py --vault /path/to/vault --apply
    python3 scripts/run-migrations.py --vault /path/to/vault --apply \\
        --migration v3.2.0-add-tars-category
"""

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path


_PLUGIN_JSON = Path(__file__).parent.parent / ".claude-plugin" / "plugin.json"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _parse_version(v: str) -> tuple[int, ...]:
    """Parse 'v3.2.0' or '3.2.0' into (3, 2, 0)."""
    v = v.lstrip("v")
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _load_plugin_version() -> str:
    try:
        data = json.loads(_PLUGIN_JSON.read_text(encoding="utf-8"))
        return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def _load_vault_version(vault: Path) -> str:
    """Read plugin_version from _system/housekeeping-state.yaml.

    Stdlib-only parser — looks for a 'plugin_version:' line anywhere in the
    file.  Returns '0.0.0' if the file is missing or the field is absent.
    """
    target = vault / "_system" / "housekeeping-state.yaml"
    if not target.is_file():
        return "0.0.0"
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return "0.0.0"
    for line in text.splitlines():
        m = re.match(r"^\s*plugin_version\s*:\s*(.+)$", line)
        if m:
            val = m.group(1).strip().strip('"').strip("'")
            if val and val not in ("null", "~", ""):
                return val
    return "0.0.0"


def _write_vault_version(vault: Path, version: str) -> None:
    """Upsert plugin_version in _system/housekeeping-state.yaml."""
    target = vault / "_system" / "housekeeping-state.yaml"
    if not target.is_file():
        return
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return

    new_lines = []
    found = False
    for line in text.splitlines():
        if re.match(r"^\s*plugin_version\s*:", line):
            leading = len(line) - len(line.lstrip())
            new_lines.append(" " * leading + f"plugin_version: {version}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"plugin_version: {version}")

    try:
        target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Migration discovery
# ---------------------------------------------------------------------------

_MIGRATION_RE = re.compile(r"^(v\d+\.\d+\.\d+)-(.+)\.py$")


def _discover_migrations() -> list[tuple[tuple[int, ...], str, Path]]:
    """Return list of (version_tuple, slug, path) sorted by version."""
    if not _MIGRATIONS_DIR.is_dir():
        return []
    results = []
    for p in _MIGRATIONS_DIR.iterdir():
        m = _MIGRATION_RE.match(p.name)
        if m:
            vtuple = _parse_version(m.group(1))
            slug = p.stem  # e.g. "v3.2.0-add-tars-category"
            results.append((vtuple, slug, p))
    results.sort(key=lambda x: x[0])
    return results


def _pending_migrations(
    vault_ver: str, plugin_ver: str
) -> list[tuple[tuple[int, ...], str, Path]]:
    """Return migrations with version > vault_ver and <= plugin_ver."""
    vault_t = _parse_version(vault_ver)
    plugin_t = _parse_version(plugin_ver)
    return [
        (vt, slug, path)
        for vt, slug, path in _discover_migrations()
        if vault_t < vt <= plugin_t
    ]


# ---------------------------------------------------------------------------
# Migration loader
# ---------------------------------------------------------------------------

def _load_migration(path: Path):
    """Import a migration module from its file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load migration: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    if not hasattr(mod, "run"):
        raise AttributeError(f"Migration {path.name} must expose a run(vault, dry_run) function")
    return mod


# ---------------------------------------------------------------------------
# Journal writer
# ---------------------------------------------------------------------------

def _write_journal(vault: Path, results: list[dict], plugin_ver: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    journal_dir = vault / "journal" / month
    journal_dir.mkdir(parents=True, exist_ok=True)
    slug_parts = "-".join(r["migration"].replace(".", "-") for r in results[:3])
    filename = f"{today}-migrations-{slug_parts}.md"
    target = journal_dir / filename

    lines = [
        "---",
        "tags: [tars/journal, tars/migration]",
        f"tars-created: {today}",
        f"tars-plugin-version: {plugin_ver}",
        "---",
        "",
        f"# Migration run — {today}",
        "",
    ]
    for r in results:
        dry = " (dry run)" if r.get("dry_run") else ""
        lines += [
            f"## {r['migration']}{dry}",
            "",
            f"- Changes: {len(r.get('changes', []))}",
            f"- Errors:  {len(r.get('errors', []))}",
            f"- Skipped: {r.get('skipped', 0)}",
            "",
        ]
        if r.get("changes"):
            lines.append("### Changes")
            for c in r["changes"][:50]:
                lines.append(f"- `{c.get('file', '?')}`: {c.get('action', '')} — {c.get('detail', '')}")
            lines.append("")
        if r.get("errors"):
            lines.append("### Errors")
            for e in r["errors"][:20]:
                lines.append(f"- `{e.get('file', '?')}`: {e.get('error', '')}")
            lines.append("")

    target.write_text("\n".join(lines), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="TARS migration runner — applies pending schema/vault-structure migrations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--vault", required=True, help="Absolute path to the vault root")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="List pending migrations and exit")
    group.add_argument("--dry-run", action="store_true", help="Simulate migrations without writing (default if neither flag given)")
    group.add_argument("--apply", action="store_true", help="Apply migrations")
    parser.add_argument(
        "--migration",
        metavar="SLUG",
        help="Run only this migration by slug (e.g. v3.2.0-add-tars-category)",
    )
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}", file=sys.stderr)
        return 1

    vault_ver = _load_vault_version(vault)
    plugin_ver = _load_plugin_version()
    pending = _pending_migrations(vault_ver, plugin_ver)

    if args.migration:
        pending = [(vt, sl, p) for vt, sl, p in pending if sl == args.migration]
        if not pending:
            print(f"Migration '{args.migration}' not found or not pending.", file=sys.stderr)
            return 1

    if args.list:
        if args.json_output:
            print(json.dumps({
                "vault_version": vault_ver,
                "plugin_version": plugin_ver,
                "pending": [sl for _, sl, _ in pending],
            }, indent=2))
        else:
            print(f"Vault version:  {vault_ver}")
            print(f"Plugin version: {plugin_ver}")
            if pending:
                print(f"\nPending ({len(pending)}):")
                for _, sl, _ in pending:
                    print(f"  {sl}")
            else:
                print("\nNo pending migrations.")
        return 0

    dry_run = not args.apply

    if not pending:
        msg = "No pending migrations."
        print(json.dumps({"status": "up_to_date", "vault_version": vault_ver}) if args.json_output else msg)
        return 0

    all_results = []
    any_error = False
    for _vt, slug, path in pending:
        try:
            mod = _load_migration(path)
        except Exception as exc:
            print(f"ERROR loading {slug}: {exc}", file=sys.stderr)
            any_error = True
            continue

        try:
            result = mod.run(vault, dry_run=dry_run)
        except Exception as exc:
            result = {"migration": slug, "dry_run": dry_run, "changes": [], "errors": [{"file": "runner", "error": str(exc)}], "skipped": 0}
            any_error = True

        if result.get("errors"):
            any_error = True

        all_results.append(result)

        if not args.json_output:
            dry_label = " [dry run]" if dry_run else ""
            print(f"\n{'='*60}")
            print(f"Migration: {slug}{dry_label}")
            print(f"  Changes: {len(result.get('changes', []))}")
            print(f"  Errors:  {len(result.get('errors', []))}")
            print(f"  Skipped: {result.get('skipped', 0)}")
            for c in result.get("changes", [])[:20]:
                print(f"    [{c.get('action', 'update')}] {c.get('file', '?')}: {c.get('detail', '')}")
            for e in result.get("errors", []):
                print(f"    [ERROR] {e.get('file', '?')}: {e.get('error', '')}")

    # Advance vault version on successful apply.
    if not dry_run and not any_error:
        _write_vault_version(vault, plugin_ver)

    # Write journal entry.
    if all_results and not dry_run:
        journal_path = _write_journal(vault, all_results, plugin_ver)
        if not args.json_output:
            print(f"\nJournal entry: {journal_path.relative_to(vault)}")

    if args.json_output:
        print(json.dumps({
            "dry_run": dry_run,
            "vault_version_before": vault_ver,
            "vault_version_after": plugin_ver if (not dry_run and not any_error) else vault_ver,
            "plugin_version": plugin_ver,
            "results": all_results,
        }, indent=2))

    return 1 if any_error else 0


if __name__ == "__main__":
    sys.exit(main())

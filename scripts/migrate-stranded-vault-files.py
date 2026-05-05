#!/usr/bin/env python3
"""Migrate files stranded by an unexpanded TARS_VAULT_PATH variable.

When .mcp.json passes "${TARS_VAULT_PATH}" as a literal string instead of an
absolute path, the tars-vault MCP server treats that as the vault root and
writes files into a directory literally named "${TARS_VAULT_PATH}" inside the
real vault.  This script finds such stranded files and moves them to their
correct locations inside the real vault.

Usage:
    python3 scripts/migrate-stranded-vault-files.py --vault /path/to/vault [--dry-run]
    python3 scripts/migrate-stranded-vault-files.py --vault /path/to/vault --apply

Options:
    --vault PATH    Absolute path to the real TARS vault root (required)
    --dry-run       Report what would be moved without touching anything (default)
    --apply         Execute the moves (writes to disk)
    --source NAME   Name of the mis-named root directory to scan
                    (default: "${TARS_VAULT_PATH}")
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


# The literal directory name that the unexpanded variable creates.
_DEFAULT_STRANDED_DIR = "${TARS_VAULT_PATH}"


def find_stranded_files(source_root: Path) -> list[tuple[Path, Path]]:
    """Return (source_path, relative_path) pairs for everything under source_root."""
    pairs = []
    if not source_root.exists():
        return pairs
    for item in source_root.rglob("*"):
        if item.is_file():
            pairs.append((item, item.relative_to(source_root)))
    return pairs


def plan_moves(
    vault: Path,
    stranded_files: list[tuple[Path, Path]],
) -> list[dict]:
    """Build a move plan, flagging conflicts where the destination already exists."""
    plan = []
    for src, rel in stranded_files:
        dst = vault / rel
        plan.append(
            {
                "src": str(src),
                "dst": str(dst),
                "rel": str(rel),
                "conflict": dst.exists(),
            }
        )
    return plan


def print_plan(plan: list[dict], dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"\n[{mode}] Stranded-file migration plan — {datetime.now():%Y-%m-%d %H:%M}\n")
    if not plan:
        print("  No stranded files found.")
        return

    conflicts = [p for p in plan if p["conflict"]]
    safe = [p for p in plan if not p["conflict"]]

    print(f"  {len(plan)} file(s) found ({len(conflicts)} conflict(s), {len(safe)} safe to move)\n")
    for p in plan:
        marker = "CONFLICT" if p["conflict"] else "move"
        print(f"  [{marker}]  {p['rel']}")
        print(f"           src: {p['src']}")
        print(f"           dst: {p['dst']}")

    if conflicts:
        print(
            f"\n  {len(conflicts)} destination(s) already exist — these will be SKIPPED even with "
            "--apply. Review manually and remove one copy before re-running."
        )


def apply_moves(plan: list[dict]) -> dict:
    moved = []
    skipped = []
    errors = []
    for p in plan:
        if p["conflict"]:
            skipped.append(p["rel"])
            continue
        src = Path(p["src"])
        dst = Path(p["dst"])
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(p["rel"])
        except Exception as exc:
            errors.append({"rel": p["rel"], "error": str(exc)})

    return {"moved": moved, "skipped": skipped, "errors": errors}


def remove_stranded_root(source_root: Path) -> bool:
    """Remove the mis-named directory if it is now empty (all levels)."""
    try:
        # Only remove if empty — never destroy unprocessed files.
        all_remaining = list(source_root.rglob("*"))
        if not any(f.is_file() for f in all_remaining):
            shutil.rmtree(source_root)
            return True
    except Exception:
        pass
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate files stranded by an unexpanded TARS_VAULT_PATH variable.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--vault", required=True, help="Absolute path to the real vault root")
    parser.add_argument(
        "--source",
        default=_DEFAULT_STRANDED_DIR,
        help=f'Name of the mis-named root directory (default: "{_DEFAULT_STRANDED_DIR}")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Report what would be moved without touching anything (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute the moves",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit results as JSON instead of human-readable text",
    )
    args = parser.parse_args()

    dry_run = not args.apply

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"ERROR: vault path does not exist or is not a directory: {vault}", file=sys.stderr)
        return 1

    source_root = vault / args.source
    stranded = find_stranded_files(source_root)
    plan = plan_moves(vault, stranded)

    if args.json_output:
        result: dict = {
            "vault": str(vault),
            "source_root": str(source_root),
            "dry_run": dry_run,
            "plan": plan,
        }
        if not dry_run:
            result["result"] = apply_moves(plan)
            if not result["result"]["errors"] and not result["result"]["skipped"]:
                result["stranded_root_removed"] = remove_stranded_root(source_root)
        print(json.dumps(result, indent=2))
        return 0

    print_plan(plan, dry_run)

    if dry_run:
        if plan:
            print(
                "\n  Run with --apply to execute the moves (conflicts are always skipped)."
            )
        return 0

    # Apply mode.
    result_data = apply_moves(plan)
    moved = result_data["moved"]
    skipped = result_data["skipped"]
    errors = result_data["errors"]

    print(f"\n  Moved:   {len(moved)}")
    print(f"  Skipped: {len(skipped)} (conflict)")
    print(f"  Errors:  {len(errors)}")
    for e in errors:
        print(f"    ERROR {e['rel']}: {e['error']}")

    if not errors and not skipped:
        removed = remove_stranded_root(source_root)
        if removed:
            print(f"\n  Removed empty stranded directory: {source_root}")
        else:
            remaining = list(source_root.rglob("*"))
            if remaining:
                print(
                    f"\n  Stranded directory still has {len(remaining)} item(s) — "
                    "not removed. Check for conflicts and re-run."
                )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

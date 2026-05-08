#!/usr/bin/env python3
"""Refresh stale `_views/*.base` files in a TARS workspace.

The plugin's `scaffold_workspace` tool stamps each generated `.base` file with
a header line `# generated-by: tars <version>`. This script reads those stamps,
compares against the live plugin version, and (by default) regenerates any
stale views — first backing the old ones up to `_views/.attic/<timestamp>/`.

Used by `/welcome --enable-obsidian`. Pass `--keep-views` to skip regeneration
and only warn on staleness.

Usage:
    python3 scripts/refresh-obsidian-views.py --vault <path> [--apply] [--keep-views]

Default is dry-run. `--apply` performs the backup+regenerate. Wraps unexpected
errors per PRD-01's user-friendly script-error contract.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _live_plugin_version() -> str:
    plugin_json = REPO_ROOT / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(plugin_json.read_text(encoding="utf-8"))["version"]
    except (OSError, KeyError, ValueError):
        return "0.0.0"


def _read_view_version(view: Path) -> str | None:
    """Returns the plugin version that generated this view, or None if no stamp."""
    try:
        with view.open(encoding="utf-8") as f:
            first = f.readline()
    except OSError:
        return None
    prefix = "# generated-by: tars "
    if first.startswith(prefix):
        return first[len(prefix):].strip()
    return None


def _source_views() -> dict[str, str]:
    """Read view templates from the plugin's repo/cache. Returns {filename: contents}.

    Looks for templates/views first, then _views as a fallback (the source repo
    ships the second; future versions may move them under templates/views).
    """
    candidates = [REPO_ROOT / "templates" / "views", REPO_ROOT / "_views"]
    for directory in candidates:
        if not directory.is_dir():
            continue
        out: dict[str, str] = {}
        for p in sorted(directory.glob("*.base")):
            try:
                out[p.name] = p.read_text(encoding="utf-8")
            except OSError:
                continue
        if out:
            return out
    return {}


def _stamp(text: str, version: str) -> str:
    if text.startswith("# generated-by: tars "):
        # replace the existing stamp line
        rest = text.split("\n", 1)[1] if "\n" in text else ""
        return f"# generated-by: tars {version}\n{rest}"
    return f"# generated-by: tars {version}\n{text}"


def scan(vault: Path, live_version: str) -> dict:
    views_dir = vault / "_views"
    summary: dict = {
        "live_version": live_version,
        "exists": views_dir.is_dir(),
        "files": [],
        "stale_count": 0,
    }
    if not views_dir.is_dir():
        return summary
    for view in sorted(views_dir.glob("*.base")):
        stamped = _read_view_version(view)
        is_stale = stamped is None or stamped != live_version
        if is_stale:
            summary["stale_count"] += 1
        summary["files"].append({
            "name": view.name,
            "stamped_version": stamped or "(unstamped)",
            "is_stale": is_stale,
        })
    return summary


def refresh(vault: Path, live_version: str, apply: bool, keep_views: bool) -> dict:
    summary = scan(vault, live_version)
    if not summary["exists"]:
        return summary
    if summary["stale_count"] == 0:
        return summary
    if keep_views:
        summary["action"] = "kept (warning only)"
        return summary

    sources = _source_views()
    if not sources:
        summary["action"] = "no source templates available"
        return summary

    views_dir = vault / "_views"
    if apply:
        attic = views_dir / ".attic" / datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        attic.mkdir(parents=True, exist_ok=True)
        # back up every existing .base file, even if not stale, so the snapshot
        # is internally consistent.
        for existing in views_dir.glob("*.base"):
            shutil.copy2(existing, attic / existing.name)
        # regenerate from sources
        for name, text in sources.items():
            (views_dir / name).write_text(_stamp(text, live_version), encoding="utf-8")
        summary["action"] = f"applied ({summary['stale_count']} stale -> regenerated, backup: {attic.relative_to(vault).as_posix()})"
        summary["attic_path"] = attic.relative_to(vault).as_posix()
    else:
        summary["action"] = "would regenerate (dry-run)"
    return summary


def _user_friendly_exit(exc: BaseException, vault: Path | None) -> int:
    if vault:
        try:
            err_dir = vault / "_system" / "telemetry"
            err_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            (err_dir / f"refresh-obsidian-views-error-{ts}.log").write_text(
                "".join(traceback.format_exception(exc)), encoding="utf-8"
            )
        except OSError:
            pass
    print("TARS refresh-obsidian-views: an unexpected error occurred.",
          file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--apply", action="store_true",
                    help="Apply changes (default is dry-run).")
    ap.add_argument("--keep-views", action="store_true",
                    help="Don't regenerate; just report staleness.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    vault = Path(args.vault).expanduser().resolve()
    if not (vault / "_system").is_dir():
        print(f"TARS refresh-obsidian-views: not a TARS workspace: {vault}",
              file=sys.stderr)
        return 1

    live = _live_plugin_version()
    summary = refresh(vault, live, apply=args.apply, keep_views=args.keep_views)
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    if not summary["exists"]:
        print("No `_views/` directory in this workspace.")
        return 0
    if summary["stale_count"] == 0:
        print(f"All {len(summary['files'])} view(s) match the live plugin version ({live}).")
        return 0
    n = summary["stale_count"]
    if args.keep_views:
        print(f"{n} view(s) generated by an older plugin version. "
              "Re-run without --keep-views to refresh.")
        return 0
    if args.apply:
        print(summary.get("action", "applied"))
        for f in summary["files"]:
            mark = "*" if f["is_stale"] else " "
            print(f"  {mark} {f['name']} (was: {f['stamped_version']})")
    else:
        print(f"{n} view(s) need refresh. Re-run with `--apply` to backup + regenerate.")
        for f in summary["files"]:
            mark = "*" if f["is_stale"] else " "
            print(f"  {mark} {f['name']} (stamped: {f['stamped_version']})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        try:
            argv = sys.argv
            i = argv.index("--vault") if "--vault" in argv else -1
            v = Path(argv[i + 1]) if i >= 0 and i + 1 < len(argv) else None
        except Exception:
            v = None
        sys.exit(_user_friendly_exit(exc, v))

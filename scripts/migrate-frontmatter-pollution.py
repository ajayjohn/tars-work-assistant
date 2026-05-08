#!/usr/bin/env python3
"""Migrate non-`tars-` frontmatter keys on imported notes to canonical equivalents.

Maps the most common bare keys to their `tars-` counterparts. Bare tags that
correspond to TARS entity types are also namespaced. Unknown keys are reported
and skipped (the user can rename them manually or extend `KEY_MAP`).

Usage:
    python3 scripts/migrate-frontmatter-pollution.py --vault <path> [--apply]

Default is dry-run. `--apply` rewrites the affected notes via direct file
writes (safer than the MCP path: this script runs before alignment is set up
on a freshly-cloned vault).

Wraps unexpected errors per PRD-01's user-friendly script-error contract.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

KEY_MAP: dict[str, str | None] = {
    # bare key  → canonical key (None means "drop entirely")
    "title": None,        # the filename / first heading already carry this
    "pm": "tars-owner",
    "owner": "tars-owner",
    "status": "tars-status",
    "state": "tars-status",
    "start": "tars-start-date",
    "end": "tars-target-date",
    "target": "tars-target-date",
    "due": "tars-due",
    "priority": "tars-priority",
    "category": "tars-category",
    "summary": "tars-summary",
    "description": "tars-summary",
    "created": "tars-created",
    "modified": "tars-modified",
    "updated": "tars-modified",
    "health": "tars-health",
}

TAG_NAMESPACE_MAP = {
    "initiative": "tars/initiative",
    "person": "tars/person",
    "decision": "tars/decision",
    "meeting": "tars/meeting",
    "task": "tars/task",
    "wisdom": "tars/wisdom",
    "vendor": "tars/vendor",
    "competitor": "tars/competitor",
    "product": "tars/product",
    "company": "tars/company",
    "journal": "tars/journal",
}

RESERVED_NON_PREFIX = {"tags", "aliases"}
SKIP_PREFIXES = ("_system/", "_views/", "archive/")
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _split(text: str) -> tuple[str | None, str]:
    m = _FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def _parse_block(block: str) -> list[tuple[str, list[str] | str | None]]:
    """Return ordered (key, value) tuples preserving file order. Lists become
    ['item', 'item']. Scalars become strings. Unparseable lines are passed
    through as raw key=None so we can re-emit them verbatim."""
    out: list[tuple[str, list[str] | str | None]] = []
    in_list: list[str] | None = None
    in_list_key: str | None = None
    for raw in block.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            out.append((f"__raw__{len(out)}", raw))
            continue
        if raw.startswith("  -") and in_list is not None:
            in_list.append(stripped[1:].strip().strip('"').strip("'"))
            continue
        in_list = None
        in_list_key = None
        if ":" not in raw:
            out.append((f"__raw__{len(out)}", raw))
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if not val:
            in_list = []
            in_list_key = key
            out.append((key, in_list))
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            items = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
            out.append((key, items))
            continue
        out.append((key, val.strip('"').strip("'")))
    return out


def _emit(entries: list[tuple[str, list[str] | str | None]]) -> str:
    lines: list[str] = []
    for key, val in entries:
        if key.startswith("__raw__"):
            lines.append(val if isinstance(val, str) else "")
            continue
        if isinstance(val, list):
            if not val:
                lines.append(f"{key}:")
            else:
                rendered = ", ".join(_quote(item) for item in val)
                lines.append(f"{key}: [{rendered}]")
        else:
            lines.append(f"{key}: {_quote(val) if val is not None else ''}")
    return "\n".join(lines)


def _quote(v: str) -> str:
    if v == "":
        return '""'
    if any(c in v for c in (":", "#", "[", "]", "'")) or " " in v and not v.startswith('"'):
        # quote anything that might confuse a stdlib YAML reader
        if '"' not in v:
            return f'"{v}"'
    return v


def _migrate_entry(entries: list[tuple[str, list[str] | str | None]]) -> tuple[list[tuple[str, list[str] | str | None]], dict]:
    """Apply KEY_MAP and TAG_NAMESPACE_MAP. Return (new_entries, report)."""
    report: dict = {"renamed": [], "dropped": [], "unmapped": [], "tags_namespaced": []}
    new_entries: list[tuple[str, list[str] | str | None]] = []
    seen_keys: set[str] = set()
    for key, val in entries:
        if key.startswith("__raw__"):
            new_entries.append((key, val))
            continue
        if key in RESERVED_NON_PREFIX or key.startswith("tars-"):
            if key == "tags" and isinstance(val, list):
                new_tags = []
                changed = False
                for t in val:
                    if t in TAG_NAMESPACE_MAP:
                        new_tags.append(TAG_NAMESPACE_MAP[t])
                        report["tags_namespaced"].append({"from": t, "to": TAG_NAMESPACE_MAP[t]})
                        changed = True
                    else:
                        new_tags.append(t)
                # de-dup while preserving order
                seen = set()
                deduped = []
                for t in new_tags:
                    if t not in seen:
                        seen.add(t)
                        deduped.append(t)
                new_entries.append((key, deduped))
                continue
            new_entries.append((key, val))
            seen_keys.add(key)
            continue
        if key in KEY_MAP:
            target = KEY_MAP[key]
            if target is None:
                report["dropped"].append(key)
                continue
            if target in seen_keys:
                # the canonical key already exists with a value; skip the bare one
                report["dropped"].append(f"{key} (duplicate of existing {target})")
                continue
            new_entries.append((target, val))
            report["renamed"].append({"from": key, "to": target})
            seen_keys.add(target)
            continue
        report["unmapped"].append(key)
        new_entries.append((key, val))
    return new_entries, report


def _is_skip(rel: Path) -> bool:
    s = rel.as_posix()
    return any(s.startswith(p) for p in SKIP_PREFIXES)


def migrate(vault: Path, apply: bool) -> dict:
    summary = {"scanned": 0, "changed": 0, "files": [], "unmapped_keys": set()}
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        if _is_skip(rel):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        block, body = _split(text)
        if block is None:
            continue
        summary["scanned"] += 1
        entries = _parse_block(block)
        new_entries, report = _migrate_entry(entries)
        if not (report["renamed"] or report["dropped"] or report["tags_namespaced"]):
            continue
        summary["changed"] += 1
        summary["files"].append({"path": rel.as_posix(), **report})
        summary["unmapped_keys"].update(report["unmapped"])
        if apply:
            new_text = "---\n" + _emit(new_entries) + "\n---\n" + body
            backup = md.with_suffix(md.suffix + ".pre-migration")
            if not backup.exists():
                shutil.copy2(md, backup)
            md.write_text(new_text, encoding="utf-8")
    summary["unmapped_keys"] = sorted(summary["unmapped_keys"])
    return summary


def _user_friendly_exit(exc: BaseException, vault: Path | None) -> int:
    if vault:
        try:
            err_dir = vault / "_system" / "telemetry"
            err_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            (err_dir / f"migrate-frontmatter-pollution-error-{ts}.log").write_text(
                "".join(traceback.format_exception(exc)), encoding="utf-8"
            )
        except OSError:
            pass
    print("TARS migrate-frontmatter-pollution: an unexpected error occurred.",
          file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--apply", action="store_true",
                    help="Write changes (default is dry-run).")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    vault = Path(args.vault).expanduser().resolve()
    if not (vault / "_system").is_dir():
        print(f"TARS migrate-frontmatter-pollution: not a TARS workspace: {vault}",
              file=sys.stderr)
        return 1
    summary = migrate(vault, apply=args.apply)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        mode = "applied" if args.apply else "dry-run"
        n = summary["changed"]
        print(f"TARS migrate-frontmatter-pollution ({mode}): {n} note(s) need changes "
              f"(scanned {summary['scanned']}).")
        for f in summary["files"]:
            print(f"  {f['path']}:")
            for r in f["renamed"]:
                print(f"    rename {r['from']!r} -> {r['to']!r}")
            for d in f["dropped"]:
                print(f"    drop  {d!r}")
            for t in f["tags_namespaced"]:
                print(f"    tag   {t['from']!r} -> {t['to']!r}")
            for u in f.get("unmapped", []):
                print(f"    skip (no mapping): {u!r}")
        if summary["unmapped_keys"]:
            print("\nUnmapped keys encountered (no rule):", ", ".join(summary["unmapped_keys"]))
        if not args.apply and n:
            print("\nRe-run with `--apply` to write the changes "
                  "(originals are preserved as <name>.md.pre-migration).")
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

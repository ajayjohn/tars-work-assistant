#!/usr/bin/env python3
"""Scan a TARS vault for notes whose frontmatter uses non-`tars-` keys.

Notes imported from outside TARS often carry bare keys like `pm:`, `status:`,
`title:`, `start:`, `end:`. Those keys are invisible to the schema-validated
search paths (`search_by_tag`'s `frontmatter_summary`, `/answer`, `/lint`),
which only surface `tars-` prefixed properties. This script lists offenders so
`/lint --fix-prefixes` (and the companion migration script) can rename them.

Usage:
    python3 scripts/lint-frontmatter-pollution.py --vault <path> [--json]

Exit code: 0 always; the count is in the output. Wraps unexpected errors per
PRD-01's user-friendly script-error contract.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

RESERVED_NON_PREFIX = {"tags", "aliases"}
SKIP_PREFIXES = ("_system/", "_views/", "archive/")
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _read_frontmatter(md: Path) -> dict | None:
    try:
        text = md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = _FM_RE.match(text)
    if not m:
        return None
    fm: dict[str, list | str | bool] = {}
    body = m.group(1)
    in_list_for: str | None = None
    for raw in body.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  -") and in_list_for:
            fm.setdefault(in_list_for, []).append(raw.split("-", 1)[1].strip())  # type: ignore[union-attr]
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if not val or val == "":
            in_list_for = key
            fm[key] = []
            continue
        in_list_for = None
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            fm[key] = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
        else:
            fm[key] = val.strip('"').strip("'")
    return fm


def _is_skip(rel: Path) -> bool:
    s = rel.as_posix()
    return any(s.startswith(p) for p in SKIP_PREFIXES)


def scan(vault: Path) -> list[dict]:
    offenders: list[dict] = []
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        if _is_skip(rel):
            continue
        fm = _read_frontmatter(md)
        if not fm:
            continue
        bad_keys = [k for k in fm.keys()
                    if k not in RESERVED_NON_PREFIX and not k.startswith("tars-")]
        if not bad_keys:
            continue
        offenders.append({
            "path": rel.as_posix(),
            "bad_keys": bad_keys,
            "tags": fm.get("tags") or [],
        })
    return offenders


def _print_human(offenders: list[dict]) -> None:
    if not offenders:
        print("No frontmatter pollution found.")
        return
    n = len(offenders)
    print(f"{n} note{'s' if n != 1 else ''} use non-TARS frontmatter keys:")
    for o in offenders:
        keys = ", ".join(o["bad_keys"])
        print(f"  {o['path']}: {keys}")


def _user_friendly_exit(exc: BaseException, vault: Path | None) -> int:
    if vault:
        try:
            err_dir = vault / "_system" / "telemetry"
            err_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            (err_dir / f"lint-frontmatter-pollution-error-{ts}.log").write_text(
                "".join(traceback.format_exception(exc)), encoding="utf-8"
            )
        except OSError:
            pass
    print("TARS lint-frontmatter-pollution: an unexpected error occurred.",
          file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    vault = Path(args.vault).expanduser().resolve()
    if not (vault / "_system").is_dir():
        print(f"TARS lint-frontmatter-pollution: not a TARS workspace: {vault}",
              file=sys.stderr)
        return 1
    offenders = scan(vault)
    if args.json:
        print(json.dumps({"count": len(offenders), "offenders": offenders}, indent=2))
    else:
        _print_human(offenders)
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

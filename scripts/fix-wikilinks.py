#!/usr/bin/env python3
"""fix-wikilinks — one-time migration to repair wikilink artifacts.

Scans all vault markdown for patterns:
  * ``[[[[Name]]|Alias]]``
  * ``[[[[Name]]]]``
  * other nested-broken variants

For each match, proposes a canonical form by looking up the alias registry and
falling back to Obsidian search. Emits a JSON diff per file for the agent to
apply via ``mcp__tars_vault__*``.

Phase 1a skeleton — detection only (no fix proposals yet). Full implementation
lands after Phase 1b per PRD §3.4.

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        default; print proposed diffs
  --apply          not honoured in the skeleton
  --json           emit machine-readable diff
Exit codes: 0 OK (with or without findings), 1 interrupted, 2 error, 3 invalid state.
"""
import argparse
import json
import re
import sys
from pathlib import Path


ARTIFACT_PATTERNS = [
    re.compile(r"\[\[\[\[[^\]]+\]\]\|[^\]]+\]\]"),   # [[[[Name]]|Alias]]
    re.compile(r"\[\[\[\[[^\]]+\]\]\]\]"),            # [[[[Name]]]]
    re.compile(r"\[\[\[[^\]]+\]\]"),                   # [[[Name]]
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fix-wikilinks")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def scan(vault: Path) -> list[dict]:
    findings: list[dict] = []
    for path in vault.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            for pattern in ARTIFACT_PATTERNS:
                for match in pattern.finditer(line):
                    findings.append(
                        {
                            "file": str(path.relative_to(vault)),
                            "line": idx,
                            "match": match.group(0),
                        }
                    )
    return findings


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3
    findings = scan(vault)
    payload = {
        "status": "skeleton",
        "vault": str(vault),
        "findings": findings,
        "proposed_fixes": [],
        "note": "Phase 1a skeleton — detection only. Phase 2 adds alias-registry resolution + diff proposals.",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"scanned: {vault}")
        print(f"findings: {len(findings)}")
        for finding in findings[:10]:
            print(f"  {finding['file']}:{finding['line']}  {finding['match']}")
        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

#!/usr/bin/env python3
"""fix-wikilinks — one-time migration to repair wikilink artifacts.

Scans all vault markdown for four patterns and applies transforms:
  1. [[[[X]]|X]]   → [[X]]             (pipe-same)
  2. [[[[X]]|Y]]   → [[X|Y]]           (pipe-diff, alias preserved)
  3. [[[X|Y]]      → [[X|Y]]           (triple-open collapses)
  4. [[[[X]]       → [[X]]             (defensive fallback)

Per-file backup: <file>.pre-v3.1-wiki-backup (never overwritten).

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        default
  --apply          actually write
  --json           emit machine-readable output
  --skip-dirs      comma-separated (default ".git,.claude,.obsidian,archive")
  --file-limit N   process at most N files (0 = all)
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PAT_PIPE_SAME = re.compile(r"\[\[\[\[([^|\]\[]+)\]\]\|\1\]\]")
PAT_PIPE_DIFF = re.compile(r"\[\[\[\[([^|\]\[]+)\]\]\|([^\]\[]+)\]\]")
PAT_TRIPLE = re.compile(r"\[\[\[([^\[\]]+?)\]\]")
PAT_QUAD_OPEN = re.compile(r"\[\[\[\[([^\[\]]+?)\]\]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fix-wikilinks")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--skip-dirs",
        default=".git,.claude,.obsidian,archive",
        help="Comma-separated top-level directory names to skip.",
    )
    parser.add_argument("--file-limit", type=int, default=0)
    return parser


def verify_clean_worktree(vault: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(vault), "status", "--porcelain"],
            capture_output=True, text=True, check=False, timeout=10,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return True, ""
    if result.returncode != 0:
        return True, ""
    if result.stdout.strip():
        return False, "vault git worktree has uncommitted changes — refuse to run"
    return True, ""


def transform(text: str) -> tuple[str, dict[str, int]]:
    counts = {"pipe_same": 0, "pipe_diff": 0, "triple_open": 0, "quad_leftover": 0}

    def sub_same(m: re.Match[str]) -> str:
        counts["pipe_same"] += 1
        return f"[[{m.group(1)}]]"

    def sub_diff(m: re.Match[str]) -> str:
        counts["pipe_diff"] += 1
        return f"[[{m.group(1)}|{m.group(2)}]]"

    def sub_quad(m: re.Match[str]) -> str:
        counts["quad_leftover"] += 1
        return f"[[{m.group(1)}]]"

    def sub_triple(m: re.Match[str]) -> str:
        counts["triple_open"] += 1
        return f"[[{m.group(1)}]]"

    text = PAT_PIPE_SAME.sub(sub_same, text)
    text = PAT_PIPE_DIFF.sub(sub_diff, text)
    text = PAT_QUAD_OPEN.sub(sub_quad, text)
    text = PAT_TRIPLE.sub(sub_triple, text)
    return text, counts


def walk(vault: Path, skip_dirs: set[str]) -> list[Path]:
    out: list[Path] = []
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        if rel.parts and rel.parts[0] in skip_dirs:
            continue
        if md.name.endswith(".pre-v3.1-wiki-backup"):
            continue
        out.append(md)
    return out


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3
    if args.apply:
        ok, err = verify_clean_worktree(vault)
        if not ok:
            print(f"error: {err}", file=sys.stderr)
            return 3
    skip_dirs = set(s.strip() for s in args.skip_dirs.split(",") if s.strip())

    totals = {"pipe_same": 0, "pipe_diff": 0, "triple_open": 0, "quad_leftover": 0}
    files_modified: list[Path] = []
    processed = 0

    for md in walk(vault, skip_dirs):
        if args.file_limit and processed >= args.file_limit:
            break
        try:
            original = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "[[[" not in original:
            continue
        new, counts = transform(original)
        if new == original:
            continue
        for k in totals:
            totals[k] += counts[k]
        files_modified.append(md)
        if args.apply:
            backup = md.with_suffix(md.suffix + ".pre-v3.1-wiki-backup")
            if not backup.exists():
                shutil.copy2(md, backup)
            md.write_text(new, encoding="utf-8")
        processed += 1

    payload: dict[str, Any] = {
        "status": "applied" if args.apply else "dry-run",
        "vault": str(vault),
        "files_modified": len(files_modified),
        "totals": totals,
        "sample_files": [str(p.relative_to(vault)) for p in files_modified[:10]],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"files modified: {payload['files_modified']}")
        print(f"substitutions: pipe_same={totals['pipe_same']} pipe_diff={totals['pipe_diff']} "
              f"triple_open={totals['triple_open']} quad_leftover={totals['quad_leftover']}")
        for f in payload["sample_files"]:
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

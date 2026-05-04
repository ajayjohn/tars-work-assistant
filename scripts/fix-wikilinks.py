#!/usr/bin/env python3
"""fix-wikilinks — repair wikilink artifacts and broken links.

Two modes (compose freely):

  Bracket-artifact repair (default; preserved from v3.1):
    1. [[[[X]]|X]]   → [[X]]             (pipe-same)
    2. [[[[X]]|Y]]   → [[X|Y]]           (pipe-diff, alias preserved)
    3. [[[X|Y]]      → [[X|Y]]           (triple-open collapses)
    4. [[[[X]]       → [[X]]             (defensive fallback)

  Broken-link repair (--repair-broken; new in v3.2 Phase 2):
    Scans every wikilink and classifies into:
      * auto_safe       — high-confidence rename (smart-quote norm; case fix
                          when exactly one vault file matches the normalized
                          basename)
      * needs_review    — multiple candidate renames; surface to /lint
      * unresolvable    — no candidate; surface to /lint as a finding
    --apply only acts on auto_safe. needs_review and unresolvable are emitted
    in the JSON report for the user to triage.

Per-file backup: <file>.pre-v3.1-wiki-backup (never overwritten).

Contract per PRD §26.15:
  --vault <path>      required
  --dry-run           default
  --apply             actually write
  --json              emit machine-readable output
  --skip-dirs         comma-separated (default ".git,.claude,.obsidian,archive")
  --file-limit N      process at most N files (0 = all)
  --repair-broken     enable broken-link repair pass in addition to bracket repair
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any


PAT_PIPE_SAME = re.compile(r"\[\[\[\[([^|\]\[]+)\]\]\|\1\]\]")
PAT_PIPE_DIFF = re.compile(r"\[\[\[\[([^|\]\[]+)\]\]\|([^\]\[]+)\]\]")
PAT_TRIPLE = re.compile(r"\[\[\[([^\[\]]+?)\]\]")
PAT_QUAD_OPEN = re.compile(r"\[\[\[\[([^\[\]]+?)\]\]")

# Permissive wikilink scanner used by --repair-broken. Different from the
# bracket-artifact patterns above; this one also captures clean links so we
# can verify their targets exist.
PAT_WIKILINK = re.compile(r"\[\[([^\[\]\n]+?)\]\]")

# Smart punctuation → ASCII map. Mirrors tars_vault.sanitize.SMART_QUOTE_MAP
# but we keep this script stdlib-only (no MCP-package import) so it can run
# from any cron environment.
SMART_QUOTE_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "′": "'", "″": '"', "–": "-", "—": "-", "…": "...",
}

_WS_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    if not text:
        return ""
    out = unicodedata.normalize("NFC", text)
    for src, dst in SMART_QUOTE_MAP.items():
        if src in out:
            out = out.replace(src, dst)
    return _WS_RE.sub(" ", out).strip()


def _split_target(raw: str) -> tuple[str, str]:
    """Split `Foo#Bar|baz` → ("Foo", "baz" or "Foo")."""
    body = raw
    display = raw
    if "|" in body:
        body, display = body.split("|", 1)
    if "#" in body:
        body = body.split("#", 1)[0]
    return body.strip(), display.strip()


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
    parser.add_argument(
        "--repair-broken",
        action="store_true",
        help="Also scan for broken wikilinks and propose canonical targets.",
    )
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


# ---------------------------------------------------------------------------
# Broken-link repair (--repair-broken)
# ---------------------------------------------------------------------------


def _build_basename_index(files: list[Path], vault: Path) -> dict[str, list[str]]:
    """Map normalized-lower basename → [actual basenames]."""
    index: dict[str, list[str]] = {}
    for md in files:
        base = md.stem
        key = _normalize(base).lower()
        if not key:
            continue
        index.setdefault(key, []).append(base)
    # De-dupe identical basenames per key.
    return {k: sorted(set(v)) for k, v in index.items()}


def _classify_target(raw: str, basename_index: dict[str, list[str]]) -> dict[str, Any]:
    """Return {bucket, original, suggestion?, candidates?} for one wikilink."""
    body, _display = _split_target(raw)
    if not body:
        return {"bucket": "unresolvable", "original": raw, "reason": "empty target"}

    # Existing target file? Clean — skip entirely. Return None bucket for
    # callers to ignore.
    normalized = _normalize(body).lower()
    candidates = basename_index.get(normalized, [])
    if body in candidates:
        return {"bucket": "ok", "original": raw}

    if not candidates:
        return {
            "bucket": "unresolvable",
            "original": raw,
            "reason": "no vault file matches the normalized basename",
        }

    if len(candidates) == 1:
        suggestion = candidates[0]
        if suggestion == body:
            return {"bucket": "ok", "original": raw}
        return {
            "bucket": "auto_safe",
            "original": raw,
            "suggestion": suggestion,
        }

    return {
        "bucket": "needs_review",
        "original": raw,
        "candidates": candidates,
    }


def _apply_repairs(text: str, repairs: list[dict[str, Any]]) -> tuple[str, int]:
    """Apply auto_safe repairs to ``text``. Returns (new_text, count_applied)."""
    if not repairs:
        return text, 0
    # Build a substitution map keyed by the original raw target. We rewrite
    # only the portion before the optional ``|display`` so display text
    # survives unchanged.
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        raw = match.group(1)
        for r in repairs:
            if r["original"] == raw:
                body, _display = _split_target(raw)
                # Reconstruct: replace body with suggestion, keep heading/display.
                tail = raw[len(body):]  # `#heading|display` or `|display` or ``
                count += 1
                return f"[[{r['suggestion']}{tail}]]"
        return match.group(0)

    new_text = PAT_WIKILINK.sub(replace, text)
    return new_text, count


def _scan_broken_links(
    files: list[Path], vault: Path, basename_index: dict[str, list[str]],
) -> dict[str, Any]:
    """Walk ``files`` and bucket every wikilink. Returns a structured report."""
    auto_safe: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    unresolvable: list[dict[str, Any]] = []
    per_file_repairs: dict[Path, list[dict[str, Any]]] = {}

    for md in files:
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "[[" not in text:
            continue
        rel = str(md.relative_to(vault))
        for match in PAT_WIKILINK.finditer(text):
            raw = match.group(1)
            classified = _classify_target(raw, basename_index)
            bucket = classified["bucket"]
            if bucket == "ok":
                continue
            entry = {"file": rel, **classified}
            if bucket == "auto_safe":
                auto_safe.append(entry)
                per_file_repairs.setdefault(md, []).append(classified)
            elif bucket == "needs_review":
                needs_review.append(entry)
            else:
                unresolvable.append(entry)

    return {
        "auto_safe": auto_safe,
        "needs_review": needs_review,
        "unresolvable": unresolvable,
        "per_file_repairs": per_file_repairs,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


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
    files = walk(vault, skip_dirs)

    for md in files:
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

    broken_report: dict[str, Any] = {}
    broken_files_modified: list[Path] = []
    if args.repair_broken:
        # Refresh the file list after bracket repair — same set, but we need
        # current contents so the scanner sees post-repair text.
        basename_index = _build_basename_index(files, vault)
        scan = _scan_broken_links(files, vault, basename_index)
        broken_report = {
            "auto_safe": scan["auto_safe"],
            "needs_review": scan["needs_review"],
            "unresolvable": scan["unresolvable"],
            "summary": {
                "auto_safe": len(scan["auto_safe"]),
                "needs_review": len(scan["needs_review"]),
                "unresolvable": len(scan["unresolvable"]),
            },
        }
        if args.apply and scan["per_file_repairs"]:
            for md, repairs in scan["per_file_repairs"].items():
                try:
                    original = md.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                new, applied = _apply_repairs(original, repairs)
                if applied and new != original:
                    backup = md.with_suffix(md.suffix + ".pre-v3.1-wiki-backup")
                    if not backup.exists():
                        shutil.copy2(md, backup)
                    md.write_text(new, encoding="utf-8")
                    broken_files_modified.append(md)

    payload: dict[str, Any] = {
        "status": "applied" if args.apply else "dry-run",
        "vault": str(vault),
        "files_modified": len(files_modified),
        "totals": totals,
        "sample_files": [str(p.relative_to(vault)) for p in files_modified[:10]],
    }
    if args.repair_broken:
        payload["repair_broken"] = broken_report
        payload["broken_files_modified"] = len(broken_files_modified)
        payload["broken_sample_files"] = [
            str(p.relative_to(vault)) for p in broken_files_modified[:10]
        ]

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"status: {payload['status']}")
        print(f"files modified: {payload['files_modified']}")
        print(f"substitutions: pipe_same={totals['pipe_same']} pipe_diff={totals['pipe_diff']} "
              f"triple_open={totals['triple_open']} quad_leftover={totals['quad_leftover']}")
        for f in payload["sample_files"]:
            print(f"  {f}")
        if args.repair_broken:
            s = broken_report.get("summary", {})
            print(
                f"broken-link scan: auto_safe={s.get('auto_safe', 0)} "
                f"needs_review={s.get('needs_review', 0)} "
                f"unresolvable={s.get('unresolvable', 0)} "
                f"applied={payload.get('broken_files_modified', 0)} files"
            )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

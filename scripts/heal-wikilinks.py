#!/usr/bin/env python3
"""TARS Wikilink Fuzzy Healer (v3.3).

Scans the vault for broken wikilinks and attempts to repair them using a
conservative three-stage pipeline:

  Stage 1 — Slug normalization
    Case-fold, collapse whitespace ↔ hyphens ↔ underscores, strip punctuation.
    If the normalized form matches exactly one file stem or alias in the vault,
    auto-fix unconditionally (confidence = exact).

  Stage 2 — Alias-registry lookup
    Consult _system/alias-registry.md for known alias → canonical mappings
    before computing edit distance. A registry hit with a unique result
    is treated as an exact match.

  Stage 3 — Levenshtein distance on normalized forms
    Distance ≤ 1 → auto-fix (very high confidence).
    Distance = 2 → suggest (user must confirm).
    Distance > 2 → skip (too ambiguous to act on).

Auto-fix rules:
  - Never auto-fix when there are multiple candidates within the threshold.
  - Always preserve the [[target|display text]] form when rewriting.
  - Every auto-applied fix is recorded in the changelog for auditability.

Usage:
    python3 scripts/heal-wikilinks.py --vault /path/to/vault [--dry-run]
    python3 scripts/heal-wikilinks.py --vault /path/to/vault --apply
    python3 scripts/heal-wikilinks.py --vault /path/to/vault --apply \\
        --focus journal     # limit to a specific subtree
    python3 scripts/heal-wikilinks.py --vault /path/to/vault --list-suggestions
        # print distance-2 suggestions without applying anything
"""

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Vault subtrees we scan by default.
_SCAN_DIRS = ["memory", "journal", "contexts", "_system/backlog", "archive/transcripts"]

# Frontmatter delimiter.
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# Wikilink pattern — captures the full inner text (target + optional |display).
_WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")

# Characters to strip when normalizing for comparison.
_PUNCT_STRIP_RE = re.compile(r"[''\".,!?;:\-_]")

# Levenshtein thresholds.
_AUTO_FIX_DISTANCE = 1
_SUGGEST_DISTANCE = 2


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

_SMART_QUOTE_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-",
}


def _fold_text(text: str) -> str:
    """Normalize for fuzzy comparison: NFC, smart-quote folding, lowercase,
    collapse whitespace/hyphens/underscores, strip punctuation."""
    out = unicodedata.normalize("NFC", text)
    for src, dst in _SMART_QUOTE_MAP.items():
        out = out.replace(src, dst)
    out = out.lower()
    # Collapse hyphens/underscores/whitespace to single space.
    out = re.sub(r"[\s\-_]+", " ", out)
    # Strip remaining punctuation.
    out = _PUNCT_STRIP_RE.sub("", out)
    return out.strip()


# ---------------------------------------------------------------------------
# Levenshtein (stdlib-only)
# ---------------------------------------------------------------------------

def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


# ---------------------------------------------------------------------------
# Vault index building
# ---------------------------------------------------------------------------

def _build_vault_index(vault: Path) -> dict[str, list[str]]:
    """Map folded-normalized basename → [original_basenames].

    Covers all .md files under the vault root (excluding .obsidian/, dotfiles).
    Aliases declared in frontmatter are also indexed under their folded form.
    """
    index: dict[str, list[str]] = {}

    def _add(key: str, canonical: str) -> None:
        index.setdefault(key, [])
        if canonical not in index[key]:
            index[key].append(canonical)

    for md_file in vault.rglob("*.md"):
        if any(p.startswith(".") for p in md_file.parts):
            continue
        stem = md_file.stem
        _add(_fold_text(stem), stem)

        # Also index aliases from frontmatter.
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        m = _FM_RE.match(text)
        if not m:
            continue
        aliases = _parse_aliases_from_yaml(m.group(1))
        for alias in aliases:
            _add(_fold_text(alias), stem)

    return index


def _parse_aliases_from_yaml(fm_text: str) -> list[str]:
    """Extract aliases list from raw frontmatter YAML text (stdlib-only)."""
    aliases: list[str] = []
    in_aliases = False
    for line in fm_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("aliases:"):
            val = stripped[len("aliases:"):].strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1]
                for item in inner.split(","):
                    item = item.strip().strip("'\"")
                    if item:
                        aliases.append(item)
                in_aliases = False
            else:
                in_aliases = True
        elif in_aliases:
            if stripped.startswith("- "):
                aliases.append(stripped[2:].strip().strip("'\""))
            elif stripped and not stripped.startswith("#"):
                in_aliases = False
    return aliases


# ---------------------------------------------------------------------------
# Alias-registry loader (stdlib-only)
# ---------------------------------------------------------------------------

_WIKILINK_INNER_RE = re.compile(r"\[\[([^\[\]\n|]+)(?:\|[^\]]*)?\]\]")


def _load_alias_registry(vault: Path) -> dict[str, str]:
    """Return folded alias → canonical_basename from _system/alias-registry.md.

    Parses markdown table rows that contain wikilinks (e.g. [[Dan Rivera]]).
    This is the same subset that alias_registry.py parses; we duplicate the
    minimal logic here to keep this script stdlib-only.
    """
    out: dict[str, str] = {}
    reg_path = vault / "_system" / "alias-registry.md"
    if not reg_path.is_file():
        return out
    try:
        text = reg_path.read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        alias_cell = cells[0].strip()
        canonical_cell = cells[1].strip()
        if alias_cell.lower() in ("alias", "short name", "abbreviation", "-", ""):
            continue
        m = _WIKILINK_INNER_RE.search(canonical_cell)
        canonical = m.group(1).strip() if m else canonical_cell
        if alias_cell and canonical:
            out[_fold_text(alias_cell)] = canonical
    return out


# ---------------------------------------------------------------------------
# Broken-link scanner
# ---------------------------------------------------------------------------

def _split_wikilink(raw: str) -> tuple[str, str | None]:
    """Split [[target|display]] → (target, display_or_None)."""
    if "|" in raw:
        target, display = raw.split("|", 1)
        return target.strip(), display.strip()
    return raw.strip(), None


def _find_broken_links(
    vault: Path,
    scan_dirs: list[str],
    vault_index: dict[str, list[str]],
) -> list[dict]:
    """Return list of {source, target, display, source_file} for unresolved wikilinks."""
    # A link is "resolved" if its folded form appears in the vault index.
    broken = []
    for scan_dir in scan_dirs:
        dir_path = vault / scan_dir
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            if any(p.startswith(".") for p in md_file.parts):
                continue
            try:
                text = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for m in _WIKILINK_RE.finditer(text):
                raw = m.group(1)
                target, display = _split_wikilink(raw)
                folded = _fold_text(target)
                if folded not in vault_index:
                    broken.append({
                        "source_file": str(md_file.relative_to(vault)),
                        "target": target,
                        "display": display,
                        "raw": raw,
                    })

    # Deduplicate by (source_file, raw).
    seen = set()
    deduped = []
    for b in broken:
        key = (b["source_file"], b["raw"])
        if key not in seen:
            seen.add(key)
            deduped.append(b)
    return deduped


# ---------------------------------------------------------------------------
# Resolution pipeline
# ---------------------------------------------------------------------------

def _resolve_link(
    target: str,
    vault_index: dict[str, list[str]],
    alias_registry: dict[str, str],
) -> dict:
    """Apply the three-stage resolution pipeline.

    Returns:
      {status: "auto", canonical, distance, stage}
      {status: "suggest", candidates: [(canonical, distance), ...]}
      {status: "unresolvable"}
    """
    folded = _fold_text(target)

    # Stage 1: exact slug-normalized match.
    if folded in vault_index:
        candidates = vault_index[folded]
        if len(candidates) == 1:
            return {"status": "auto", "canonical": candidates[0], "distance": 0, "stage": "exact"}
        # Multiple exact matches — ambiguous.
        return {"status": "suggest", "candidates": [(c, 0) for c in candidates]}

    # Stage 2: alias-registry lookup.
    if folded in alias_registry:
        canonical = alias_registry[folded]
        return {"status": "auto", "canonical": canonical, "distance": 0, "stage": "alias-registry"}

    # Stage 3: Levenshtein on all indexed keys.
    auto_candidates: list[tuple[str, int]] = []   # (canonical, distance)
    suggest_candidates: list[tuple[str, int]] = []

    for key, basenames in vault_index.items():
        dist = _levenshtein(folded, key)
        for basename in basenames:
            if dist <= _AUTO_FIX_DISTANCE:
                auto_candidates.append((basename, dist))
            elif dist <= _SUGGEST_DISTANCE:
                suggest_candidates.append((basename, dist))

    # De-duplicate by canonical (keep lowest distance).
    def _dedup(pairs: list[tuple[str, int]]) -> list[tuple[str, int]]:
        seen: dict[str, int] = {}
        for canonical, dist in pairs:
            if canonical not in seen or dist < seen[canonical]:
                seen[canonical] = dist
        return sorted(seen.items(), key=lambda x: x[1])

    auto_candidates = _dedup(auto_candidates)
    suggest_candidates = _dedup(suggest_candidates)

    if len(auto_candidates) == 1:
        canonical, dist = auto_candidates[0]
        return {"status": "auto", "canonical": canonical, "distance": dist, "stage": f"levenshtein-{dist}"}
    if len(auto_candidates) > 1:
        # Multiple auto-fix candidates — demote to suggest for safety.
        return {"status": "suggest", "candidates": auto_candidates}

    if suggest_candidates:
        return {"status": "suggest", "candidates": suggest_candidates}

    return {"status": "unresolvable"}


# ---------------------------------------------------------------------------
# File rewriter
# ---------------------------------------------------------------------------

def _rewrite_link(raw: str, new_target: str) -> str:
    """Rewrite a wikilink, preserving display text if present.

    [[old_target]] → [[new_target]]
    [[old_target|display]] → [[new_target|display]]
    """
    _, display = _split_wikilink(raw)
    if display:
        return f"[[{new_target}|{display}]]"
    return f"[[{new_target}]]"


def _apply_fixes_to_file(
    vault: Path,
    source_file: str,
    fixes: list[dict],
) -> tuple[int, str | None]:
    """Apply a list of {raw, new_target} fixes to a file.

    Returns (fix_count, error_message_or_None).
    """
    path = vault / source_file
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return 0, str(exc)

    new_text = text
    applied = 0
    for fix in fixes:
        raw = fix["raw"]
        new_target = fix["new_target"]
        old_wikilink = f"[[{raw}]]"
        new_wikilink = _rewrite_link(raw, new_target)
        if old_wikilink in new_text:
            new_text = new_text.replace(old_wikilink, new_wikilink)
            applied += 1

    if new_text == text:
        return 0, None

    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        return 0, str(exc)

    return applied, None


# ---------------------------------------------------------------------------
# Changelog writer
# ---------------------------------------------------------------------------

def _write_changelog(vault: Path, fixes: list[dict]) -> None:
    """Append auto-fix events to _system/changelog/YYYY-MM-DD.md."""
    if not fixes:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    changelog_dir = vault / "_system" / "changelog"
    changelog_dir.mkdir(parents=True, exist_ok=True)
    target = changelog_dir / f"{today}.md"
    lines = [
        f"\n## heal-wikilinks run — {datetime.now().strftime('%H:%M')}",
        f"Auto-fixed {len(fixes)} wikilink(s):\n",
    ]
    for fix in fixes:
        lines.append(
            f"- `{fix['source_file']}`: `[[{fix['raw']}]]` → `[[{fix['new_target']}]]` "
            f"(stage={fix['stage']}, dist={fix['distance']})"
        )
    lines.append("")
    try:
        with target.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="TARS wikilink fuzzy healer — auto-repairs broken links.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--vault", required=True, help="Absolute path to the vault root")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", default=True,
                      help="Report proposed fixes without writing (default)")
    mode.add_argument("--apply", action="store_true",
                      help="Apply auto-fix candidates and log them to changelog")
    mode.add_argument("--list-suggestions", action="store_true",
                      help="Print distance-2 suggestions only; do not apply")
    parser.add_argument("--focus", metavar="SUBDIR",
                        help="Limit scan to a specific subdirectory (e.g. journal)")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Emit results as JSON")
    parser.add_argument("--max-auto", type=int, default=200,
                        help="Safety cap on auto-fixes per run (default: 200)")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"ERROR: vault not found: {vault}", file=sys.stderr)
        return 1

    dry_run = not args.apply
    scan_dirs = [args.focus] if args.focus else _SCAN_DIRS

    # Build indexes.
    vault_index = _build_vault_index(vault)
    alias_reg = _load_alias_registry(vault)

    # Find broken links.
    broken = _find_broken_links(vault, scan_dirs, vault_index)

    # Resolve each broken link.
    auto_fixes: list[dict] = []
    suggestions: list[dict] = []
    unresolvable: list[dict] = []

    for b in broken:
        resolution = _resolve_link(b["target"], vault_index, alias_reg)
        if resolution["status"] == "auto":
            auto_fixes.append({**b, **resolution, "new_target": resolution["canonical"]})
        elif resolution["status"] == "suggest":
            suggestions.append({**b, "candidates": resolution["candidates"]})
        else:
            unresolvable.append(b)

    # Safety cap.
    if len(auto_fixes) > args.max_auto:
        print(
            f"WARNING: {len(auto_fixes)} auto-fixes found, capped at {args.max_auto}. "
            "Run again after reviewing to process the rest.",
            file=sys.stderr,
        )
        auto_fixes = auto_fixes[: args.max_auto]

    if args.json_output:
        print(json.dumps({
            "dry_run": dry_run,
            "auto_fixes": auto_fixes,
            "suggestions": [
                {**s, "candidates": [{"canonical": c, "distance": d} for c, d in s["candidates"]]}
                for s in suggestions
            ],
            "unresolvable": unresolvable,
        }, indent=2))
        if not dry_run and not args.list_suggestions:
            _do_apply(vault, auto_fixes)
        return 0

    # Human-readable output.
    label = "DRY RUN" if dry_run else "APPLY"
    if args.list_suggestions:
        label = "SUGGESTIONS"
    print(f"\n[{label}] heal-wikilinks — {vault}\n")
    print(f"  Broken links found:  {len(broken)}")
    print(f"  Auto-fixable:        {len(auto_fixes)}")
    print(f"  Needs review:        {len(suggestions)}")
    print(f"  Unresolvable:        {len(unresolvable)}")

    if auto_fixes and not args.list_suggestions:
        print(f"\n  Auto-fixes ({'would apply' if dry_run else 'applying'}):")
        for fix in auto_fixes:
            print(
                f"    [{fix['stage']}] {fix['source_file']}\n"
                f"      [[{fix['raw']}]]  →  [[{fix['new_target']}]]"
            )

    if suggestions:
        print(f"\n  Suggestions (review required — distance 2):")
        for i, s in enumerate(suggestions[:50], 1):
            cands = ", ".join(f"{c} (dist={d})" for c, d in s["candidates"][:3])
            print(f"    {i}. {s['source_file']}: [[{s['target']}]] → candidates: {cands}")
        if len(suggestions) > 50:
            print(f"    ... and {len(suggestions)-50} more")

    if not dry_run and not args.list_suggestions:
        _do_apply(vault, auto_fixes)
        if auto_fixes:
            print(f"\n  Applied {len(auto_fixes)} fix(es). Changelog updated.")
    elif dry_run and auto_fixes:
        print(f"\n  Run with --apply to execute {len(auto_fixes)} auto-fix(es).")

    return 0


def _do_apply(vault: Path, auto_fixes: list[dict]) -> None:
    """Group fixes by file and apply, then write changelog."""
    # Group by source file.
    by_file: dict[str, list[dict]] = {}
    for fix in auto_fixes:
        by_file.setdefault(fix["source_file"], []).append(fix)

    applied_fixes = []
    for source_file, fixes in by_file.items():
        count, err = _apply_fixes_to_file(vault, source_file, fixes)
        if err:
            print(f"  ERROR applying to {source_file}: {err}", file=sys.stderr)
        else:
            applied_fixes.extend(fixes[:count])

    _write_changelog(vault, applied_fixes)


if __name__ == "__main__":
    sys.exit(main())

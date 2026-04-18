"""scan_secrets — Classify content against _system/guardrails.yaml patterns.

Wraps scripts/scan-secrets.py when available; falls back to an in-process
scan using the same guardrails.yaml patterns.

Arguments:
  vault:   required.
  content: required. String to classify. Can be a note body, a task title,
           anything a write-path skill is about to persist.

Returns:
  {status: ok, classification: "clean" | "warn" | "block",
   hits: [{severity, category, pattern, sample}],
   total: N}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .. import _common


def _load_patterns(vault: Path) -> dict[str, list[dict]]:
    path = vault / "_system" / "guardrails.yaml"
    if not path.is_file():
        return {"block": [], "warn": []}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"block": [], "warn": []}
    buckets: dict[str, list[dict]] = {"block": [], "warn": []}
    current: str | None = None
    for raw in text.split("\n"):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in ("block_patterns:", "warn_patterns:"):
            current = "block" if "block" in stripped else "warn"
            continue
        # New list item — may carry name (and optionally pattern) on same line.
        list_item = re.match(r"^\s+-\s*(.*)$", raw)
        if list_item and current:
            rest = list_item.group(1)
            name_match = re.search(r"name:\s*([^,\n]+?)\s*(?:,|$)", rest)
            pat_match = re.search(r"pattern:\s*(.+?)\s*$", rest)
            name = (
                name_match.group(1).strip().strip('"').strip("'")
                if name_match
                else ""
            )
            pattern = None
            if pat_match:
                pattern = pat_match.group(1).strip().strip('"').strip("'")
            buckets[current].append({"name": name, "pattern": pattern})
            continue
        # Indented continuation line (pattern: on its own)
        cont = re.match(r"^\s+(name|pattern):\s*(.+?)\s*$", raw)
        if cont and current and buckets[current]:
            key = cont.group(1)
            val = cont.group(2).strip().strip('"').strip("'")
            buckets[current][-1][key] = val
    # Drop entries missing a pattern
    for k in buckets:
        buckets[k] = [e for e in buckets[k] if e.get("pattern")]
    return buckets


def scan_secrets(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    content = kwargs.get("content")
    if not vault:
        return _common.error("missing 'vault'")
    if not isinstance(content, str):
        return _common.error("missing 'content' (str)")
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    patterns = _load_patterns(vault_p)
    hits: list[dict[str, Any]] = []
    worst = "clean"
    for sev in ("block", "warn"):
        for entry in patterns.get(sev, []):
            pat = entry.get("pattern")
            if not pat:
                continue
            try:
                rx = re.compile(pat)
            except re.error:
                continue
            for m in rx.finditer(content):
                sample = m.group(0)
                if len(sample) > 80:
                    sample = sample[:77] + "..."
                hits.append({
                    "severity": sev,
                    "name": entry.get("name", ""),
                    "pattern": pat,
                    "sample": sample,
                })
                if sev == "block":
                    worst = "block"
                elif worst != "block":
                    worst = "warn"

    return _common.ok(classification=worst, hits=hits, total=len(hits))

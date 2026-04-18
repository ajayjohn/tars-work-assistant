"""classify_file — Propose a taxonomy target path for a loose vault file.

Rules (narrow first-pass; PRD §3.7 is aspirational for later):
  * *Resume.md                        → contexts/people/<slug>/
  * *-Walkthrough-*.md, *-Meeting-*.md → contexts/events/<first-token-slug>/
                                          OR contexts/people/<slug>/ if first
                                          token resolves as a person tag
  * *DBI*, *data-hub*                 → contexts/initiatives/<slug>/
  * *-research*, *research*           → contexts/research/YYYY-MM/
  * Anything else                     → contexts/misc/  (flagged low-confidence)

Arguments:
  vault: required.
  path:  required. Vault-relative file path to classify.

Returns:
  {status: ok, source, proposed, confidence, rationale}
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from .. import _common


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def classify_file(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    path = kwargs.get("path")
    if not vault:
        return _common.error("missing 'vault'")
    if not path:
        return _common.error("missing 'path'")
    try:
        vault_p = _common.resolve_vault_path(vault)
        src = _common.resolve_note_path(vault_p, path)
    except ValueError as exc:
        return _common.error(str(exc))
    if not src.is_file():
        return _common.error(f"file not found: {src.relative_to(vault_p)}")

    name = src.name
    stem = src.stem
    low = stem.lower()

    proposed = f"contexts/misc/{name}"
    rationale = "fallback (low confidence)"
    confidence = 0.3

    if low.endswith("resume") or "resume" in low.split():
        token = stem.replace(" Resume", "").replace("-Resume", "").replace("_Resume", "")
        proposed = f"contexts/people/{_slug(token)}/{name}"
        rationale = "*Resume.md → people folder"
        confidence = 0.9
    elif re.search(r"-walkthrough-|-walkthrough-", low):
        token = re.split(r"-walkthrough", stem, maxsplit=1)[0]
        proposed = f"contexts/people/{_slug(token)}/{name}"
        rationale = "*-Walkthrough-*.md → person prep folder"
        confidence = 0.85
    elif re.search(r"-meeting-|monday-meeting|weekly-meeting", low):
        proposed = f"contexts/events/{_slug(stem)[:40] or 'misc'}/{name}"
        rationale = "*-Meeting-*.md → event folder"
        confidence = 0.75
    elif re.search(r"\bdbi\b|data-hub|data_hub", low):
        proposed = f"contexts/initiatives/DBI/{name}"
        rationale = "DBI/data-hub keyword match"
        confidence = 0.8
    elif re.search(r"research|strategy|roadmap", low):
        today = date.today()
        proposed = f"contexts/research/{today.year:04d}-{today.month:02d}/{name}"
        rationale = "research/strategy/roadmap keyword match"
        confidence = 0.7
    elif re.search(r"screening|interview|\bcv\b", low):
        token = re.split(r"\b(screening|interview)\b", stem, maxsplit=1, flags=re.I)[0].strip(" -_")
        proposed = f"contexts/people/{_slug(token)}/{name}"
        rationale = "screening/interview → person folder"
        confidence = 0.7

    return _common.ok(
        source=str(src.relative_to(vault_p)),
        proposed=proposed,
        confidence=confidence,
        rationale=rationale,
    )

"""move_note — Move a note in the vault, rewriting path-qualified wikilinks.

Obsidian resolves bare-filename wikilinks globally, so moves that preserve
filename are safe. But path-qualified refs (e.g. `[[folder/old-name]]`,
`[[folder/old-name|alias]]`) need rewriting. This tool handles both paths.

Arguments:
  vault:   required.
  src:     required. Vault-relative source path.
  dst:     required. Vault-relative destination path.
  rewrite_wikilinks: optional bool (default true).

Returns:
  {status: ok, from, to, references_rewritten: N}
  {status: error, reason}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .. import _common
from ..telemetry import append_event


SKIP_DIRS = {".git", ".obsidian", ".claude"}


def move_note(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    src = kwargs.get("src")
    dst = kwargs.get("dst")
    rewrite = bool(kwargs.get("rewrite_wikilinks", True))
    if not vault:
        return _common.error("missing 'vault'")
    if not src or not dst:
        return _common.error("missing 'src' and/or 'dst'")
    try:
        vault_p = _common.resolve_vault_path(vault)
        src_p = _common.resolve_note_path(vault_p, src)
        dst_p = _common.resolve_note_path(vault_p, dst)
    except ValueError as exc:
        return _common.error(str(exc))

    if not src_p.is_file():
        return _common.error(f"source not found: {src_p.relative_to(vault_p)}")
    if dst_p.exists():
        return _common.error(f"destination already exists: {dst_p.relative_to(vault_p)}")

    dst_p.parent.mkdir(parents=True, exist_ok=True)
    src_p.rename(dst_p)

    refs_rewritten = 0
    if rewrite:
        src_rel_no_ext = str(src_p.relative_to(vault_p)).removesuffix(".md")
        dst_rel_no_ext = str(dst_p.relative_to(vault_p)).removesuffix(".md")
        # Patterns: [[path]], [[path|alias]]
        # We only rewrite path-qualified forms — bare filename wikilinks
        # (e.g. [[2026-03-22]]) don't need rewriting.
        pat_plain = re.compile(
            r"\[\[" + re.escape(src_rel_no_ext) + r"\]\]"
        )
        pat_piped = re.compile(
            r"\[\[" + re.escape(src_rel_no_ext) + r"(\|[^\]]+)\]\]"
        )
        for md in vault_p.rglob("*.md"):
            rel = md.relative_to(vault_p)
            if any(str(rel).startswith(s) for s in SKIP_DIRS):
                continue
            if md.resolve() == dst_p.resolve():
                # Don't touch the just-moved file.
                continue
            try:
                text = md.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if src_rel_no_ext not in text:
                continue
            new_text, n1 = pat_plain.subn(f"[[{dst_rel_no_ext}]]", text)
            new_text, n2 = pat_piped.subn(
                lambda m: f"[[{dst_rel_no_ext}{m.group(1)}]]", new_text
            )
            if n1 + n2 > 0:
                md.write_text(new_text, encoding="utf-8")
                refs_rewritten += n1 + n2

    append_event(
        vault_p,
        {
            "event": "vault_write",
            "tool": "move_note",
            "src": str(src_p.relative_to(vault_p)),
            "dst": str(dst_p.relative_to(vault_p)),
            "references_rewritten": refs_rewritten,
        },
    )
    return _common.ok(
        **{
            "from": str(src_p.relative_to(vault_p)),
            "to": str(dst_p.relative_to(vault_p)),
            "references_rewritten": refs_rewritten,
        }
    )

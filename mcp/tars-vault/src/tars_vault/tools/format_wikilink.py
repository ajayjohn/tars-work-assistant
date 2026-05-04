"""format_wikilink — resolve raw text to an Obsidian-safe wikilink.

Arguments (all via kwargs):
  vault:  required. Absolute vault path (auto-injected by the server).
  text:   required. The reference text the caller wants to link to.
  kind:   optional. Entity kind hint: person, vendor, competitor, product,
          initiative, decision, org-context. Restricts alias lookups.

Returns the dict produced by :func:`tars_vault.wikilink.format_wikilink`.
See that module for the full status taxonomy.
"""
from __future__ import annotations

from typing import Any

from .. import _common
from ..wikilink import format_wikilink as _format_wikilink


def format_wikilink(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    text = kwargs.get("text")
    kind = kwargs.get("kind")

    if not vault:
        return _common.error("missing 'vault' path")
    if text is None:
        return _common.error("missing 'text' argument")
    if not isinstance(text, str):
        return _common.error("'text' must be a string")

    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    return _format_wikilink(text, vault=vault_p, kind=kind)

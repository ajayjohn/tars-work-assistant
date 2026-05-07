"""resolve_alias — Resolve short names and abbreviations to canonical records."""
from __future__ import annotations

from typing import Any

from .. import _common, alias_registry
from ..sanitize import normalize_text


def _candidate(entry: alias_registry.AliasEntry) -> dict[str, Any]:
    return {
        "alias": entry.alias,
        "canonical": entry.canonical,
        "wikilink": f"[[{entry.canonical}]]",
        "kind": entry.kind,
        "contexts": [
            {"keyword": keyword, "canonical": canonical, "wikilink": f"[[{canonical}]]"}
            for keyword, canonical in entry.contexts
        ],
    }


def resolve_alias(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    name = kwargs.get("name") or kwargs.get("alias")
    kind = kwargs.get("kind") or kwargs.get("kind_hint")
    context = kwargs.get("context")

    if not vault:
        return _common.error("missing 'vault'")
    if not name or not isinstance(name, str):
        return _common.error("missing 'name'")

    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    matches = alias_registry.lookup(vault_p, name, kind_hint=kind)
    if not matches:
        return _common.ok(
            resolution_status="unresolved",
            name=name,
            canonical=None,
            wikilink=None,
            candidates=[],
            reason="No alias registry entry matched.",
        )

    if context:
        needle = normalize_text(str(context)).lower()
        context_matches: list[dict[str, Any]] = []
        for entry in matches:
            for keyword, canonical in entry.contexts:
                if keyword and keyword in needle:
                    context_matches.append(
                        {
                            "alias": entry.alias,
                            "canonical": canonical,
                            "wikilink": f"[[{canonical}]]",
                            "kind": entry.kind,
                            "matched_context": keyword,
                        }
                    )
        if len(context_matches) == 1:
            return _common.ok(resolution_status="resolved", **context_matches[0])
        if len(context_matches) > 1:
            return _common.ok(
                resolution_status="ambiguous",
                name=name,
                candidates=context_matches,
                reason="Multiple context overrides matched.",
            )

    unique: dict[str, alias_registry.AliasEntry] = {entry.canonical: entry for entry in matches}
    if len(unique) == 1:
        entry = next(iter(unique.values()))
        return _common.ok(resolution_status="resolved", **_candidate(entry))

    return _common.ok(
        resolution_status="ambiguous",
        name=name,
        candidates=[_candidate(entry) for entry in matches],
        reason="Multiple aliases matched; provide more context.",
    )

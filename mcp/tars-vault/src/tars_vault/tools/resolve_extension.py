"""resolve_extension — Match enabled workspace extensions for a core workflow."""
from __future__ import annotations

from typing import Any

from .. import _common
from . import extension_common as ext


def resolve_extension(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    if not vault:
        return _common.error("missing 'vault'")
    vault_p = _common.resolve_vault_path(vault)
    skill = kwargs.get("skill")
    mode = kwargs.get("mode")
    capability = kwargs.get("capability")
    provider = kwargs.get("provider")
    tool_names = kwargs.get("tool_names") or []
    if isinstance(tool_names, str):
        tool_names = [tool_names]
    tool_names = [str(t) for t in tool_names]

    matches: list[dict[str, Any]] = []
    for extension_id, entry in sorted(ext.registry_entries(vault_p).items()):
        if not isinstance(entry, dict) or not entry.get("enabled", False):
            continue
        path = entry.get("path")
        if not path:
            continue
        target, path_error = ext.safe_workspace_relative_path(vault_p, str(path))
        if path_error or target is None:
            continue
        manifest, errors, warnings = ext.validate_manifest(vault_p, target)
        if errors:
            continue
        matched, score, reasons = ext.match_extension(
            manifest,
            skill=str(skill) if skill else None,
            mode=str(mode) if mode else None,
            capability=str(capability) if capability else None,
            provider=str(provider) if provider else None,
            tool_names=tool_names,
        )
        if not matched:
            continue
        entrypoints = manifest.get("entrypoints") if isinstance(manifest.get("entrypoints"), dict) else {}
        matches.append(
            {
                "id": extension_id,
                "score": score,
                "reasons": reasons,
                "root": "workspace",
                "path": target.relative_to(vault_p).as_posix(),
                "type": manifest.get("type"),
                "version": manifest.get("version"),
                "capabilities": manifest.get("capabilities", []),
                "entrypoints": entrypoints,
                "warnings": warnings,
            }
        )

    matches.sort(key=lambda item: (-int(item["score"]), str(item["id"])))
    return _common.ok(
        matches=matches,
        selected=matches[0] if len(matches) == 1 else None,
        ambiguous=len(matches) > 1 and matches[0]["score"] == matches[1]["score"],
    )


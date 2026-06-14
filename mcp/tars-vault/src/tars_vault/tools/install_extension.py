"""install_extension — Copy an extension source into the workspace extension root."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from . import extension_common as ext


def install_extension(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    source_path = kwargs.get("source_path")
    source = str(kwargs.get("source") or "local").strip()
    enable = bool(kwargs.get("enable", False))
    if not vault:
        return _common.error("missing 'vault'")
    if not source_path:
        return _common.error("missing 'source_path'")
    vault_p = _common.resolve_vault_path(vault)
    source_p = Path(str(source_path)).expanduser().resolve()
    manifest, errors, warnings = ext.install_from_source(vault_p, source_p, enable, source)
    if errors:
        return _common.error("extension install failed validation", errors=errors, warnings=warnings)
    return _common.ok(
        id=manifest.get("id"),
        version=manifest.get("version"),
        enabled=enable,
        source=source,
        path=ext.registry_entries(vault_p).get(str(manifest.get("id")), {}).get("path"),
        warnings=warnings,
    )


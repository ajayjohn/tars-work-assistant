"""scaffold_extension — Create a disabled workspace extension skeleton."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import _common
from . import extension_common as ext


def scaffold_extension(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    extension_id = str(kwargs.get("extension_id") or kwargs.get("id") or "").strip()
    name = str(kwargs.get("name") or extension_id or "Untitled Extension").strip()
    ext_type = str(kwargs.get("type") or "provider-adapter").strip()
    capability = str(kwargs.get("capability") or "").strip()
    skills = kwargs.get("skills") or []
    modes = kwargs.get("modes") or []
    enable = bool(kwargs.get("enable", False))
    overwrite = bool(kwargs.get("overwrite", False))
    if not vault:
        return _common.error("missing 'vault'")
    if not extension_id:
        return _common.error("missing 'extension_id'")
    if ext_type not in ext.ALLOWED_TYPES:
        return _common.error(f"unsupported extension type: {ext_type}")
    if isinstance(skills, str):
        skills = [skills]
    if isinstance(modes, str):
        modes = [modes]
    vault_p = _common.resolve_vault_path(vault)
    target = ext.extension_dir_from_id(vault_p, extension_id)
    if target.exists() and not overwrite:
        return _common.error("extension directory already exists", path=target.relative_to(vault_p).as_posix())

    target.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": extension_id,
        "name": name,
        "version": "0.1.0",
        "tars_extension_version": ext.EXTENSION_SCHEMA_VERSION,
        "type": ext_type,
        "status": "enabled" if enable else "disabled",
        "capabilities": [capability] if capability else [],
        "applies_to": {
            "skills": [str(s) for s in skills],
            "modes": [str(m) for m in modes],
        },
        "entrypoints": {"instructions": "instructions.md"},
        "safety": {
            "requires_review": True,
            "may_write_workspace": False,
            "may_mutate_external_provider": False,
        },
    }
    (target / "extension.yaml").write_text(ext.dump_yaml(manifest), encoding="utf-8")
    (target / "instructions.md").write_text(
        f"# {name}\n\nDescribe when the parent TARS skill should use this extension, "
        "what tools it may inspect, and what review proposals it should emit.\n",
        encoding="utf-8",
    )
    manifest, errors, warnings = ext.validate_manifest(vault_p, target)
    if errors:
        return _common.error("scaffolded extension failed validation", errors=errors, warnings=warnings)

    registry = ext.load_registry(vault_p)
    entries = registry.setdefault("extensions", {})
    entries[extension_id] = {
        "enabled": enable,
        "source": "local",
        "root": "workspace",
        "path": target.relative_to(vault_p).as_posix(),
        "installed_version": "0.1.0",
    }
    ext.write_registry(vault_p, registry)
    return _common.ok(
        id=extension_id,
        path=target.relative_to(vault_p).as_posix(),
        enabled=enable,
        warnings=warnings,
    )


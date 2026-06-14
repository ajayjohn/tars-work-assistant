"""read_extension — Read an approved file from a registered workspace extension."""
from __future__ import annotations

from typing import Any

from .. import _common
from . import extension_common as ext


def read_extension(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    extension_id = kwargs.get("extension_id") or kwargs.get("id")
    file = kwargs.get("file")
    max_chars = int(kwargs.get("max_chars") or 100000)
    if not vault:
        return _common.error("missing 'vault'")
    if not extension_id:
        return _common.error("missing 'extension_id'")
    vault_p = _common.resolve_vault_path(vault)
    manifest, target, error = ext.read_entrypoint(vault_p, str(extension_id), str(file) if file else None)
    if error or target is None:
        return _common.error(error or "extension file unavailable")
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return _common.error(f"could not read extension file: {exc}")
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars]
    return _common.ok(
        id=manifest.get("id"),
        path=target.relative_to(vault_p).as_posix(),
        content=text,
        truncated=truncated,
    )


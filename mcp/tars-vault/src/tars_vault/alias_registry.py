"""In-process alias-registry cache with file-mtime invalidation. Skeleton."""
from pathlib import Path


REGISTRY_RELATIVE = "_system/alias-registry.md"


def registry_path(vault: Path) -> Path:
    return Path(vault) / REGISTRY_RELATIVE

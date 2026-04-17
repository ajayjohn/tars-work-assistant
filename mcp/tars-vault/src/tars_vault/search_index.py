"""FTS5 + sqlite-vec access layer. Skeleton for Phase 1a; impl lands Phase 4."""
from pathlib import Path


INDEX_DB_RELATIVE = "_system/search.db"


def index_path(vault: Path) -> Path:
    return Path(vault) / INDEX_DB_RELATIVE

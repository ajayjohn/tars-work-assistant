"""detect_near_duplicates — Identify likely-duplicate notes within a folder.

Similarity signals:
  * Content SHA-256 (exact duplicates)
  * Normalized filename (whitespace + hyphen folding)
  * First-1000-byte body hash (near-dup with different prefix / frontmatter)

Arguments:
  vault: required.
  folder: optional (default "contexts/artifacts"). Vault-relative.
  min_cluster: optional int (default 2).

Returns:
  {status: ok, clusters: [{signal, files: [...]}, ...]}
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .. import _common


def _norm_name(name: str) -> str:
    base = name.removesuffix(".md")
    return re.sub(r"[\s_\-]+", "-", base.lower())


def _body_only(text: str) -> str:
    _fm, body = _common.split_frontmatter(text)
    return body.strip()


def detect_near_duplicates(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    folder = kwargs.get("folder", "contexts/artifacts")
    min_cluster = int(kwargs.get("min_cluster", 2))
    if not vault:
        return _common.error("missing 'vault'")
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))
    target = (vault_p / folder).resolve()
    try:
        target.relative_to(vault_p)
    except ValueError:
        return _common.error("folder escapes vault")
    if not target.is_dir():
        return _common.error(f"folder not found: {folder}")

    by_sha: dict[str, list[str]] = defaultdict(list)
    by_norm_name: dict[str, list[str]] = defaultdict(list)
    by_body_prefix: dict[str, list[str]] = defaultdict(list)

    for md in target.rglob("*.md"):
        rel = str(md.relative_to(vault_p))
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        by_sha[sha].append(rel)
        by_norm_name[_norm_name(md.name)].append(rel)
        body_prefix = _body_only(text)[:1000].encode("utf-8")
        if body_prefix:
            bh = hashlib.sha256(body_prefix).hexdigest()[:16]
            by_body_prefix[bh].append(rel)

    clusters = []
    for sha, files in by_sha.items():
        if len(files) >= min_cluster:
            clusters.append({"signal": "sha256-exact", "key": sha, "files": files})
    for name, files in by_norm_name.items():
        if len(files) >= min_cluster and not _has_cluster(clusters, files):
            clusters.append({"signal": "filename-normalized", "key": name, "files": files})
    for bh, files in by_body_prefix.items():
        if len(files) >= min_cluster and not _has_cluster(clusters, files):
            clusters.append({"signal": "body-prefix-1000", "key": bh, "files": files})

    return _common.ok(folder=folder, cluster_count=len(clusters), clusters=clusters)


def _has_cluster(existing: list[dict], files: list[str]) -> bool:
    fs = set(files)
    for c in existing:
        if fs == set(c["files"]):
            return True
    return False

"""Shared helpers for tars-vault tool handlers.

Stdlib-only frontmatter parser with graceful fallback. Handles the
subset of YAML that TARS frontmatter actually uses (scalars, lists,
nested mappings one level deep). Full PyYAML is not a dependency.

All tools read/write UTF-8. All file paths are relative to the vault root.
"""
from __future__ import annotations

import io
import json
import re
import shutil
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def resolve_vault_path(vault: str | Path) -> Path:
    """Normalize a vault path argument to an absolute, resolved Path."""
    return Path(vault).expanduser().resolve()


def resolve_note_path(vault: Path, file_or_path: str) -> Path:
    """Given a vault root + a note reference, return the absolute note path.

    Accepts:
      * vault-relative path with or without .md extension
      * bare filename (resolves to first match under memory/ or journal/)
    """
    vault = Path(vault)
    candidate = file_or_path
    if not candidate.endswith(".md"):
        candidate = candidate + ".md"
    p = (vault / candidate).resolve()
    # Must stay inside the vault
    try:
        p.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"path escapes vault: {file_or_path}") from exc
    return p


# ---------------------------------------------------------------------------
# Frontmatter parser (stdlib-only)
# ---------------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Return (frontmatter_dict | None, body). Missing/invalid FM → (None, text)."""
    m = _FM_RE.match(text)
    if not m:
        return None, text
    fm = parse_simple_yaml(m.group(1))
    body = text[m.end():]
    return fm, body


def parse_simple_yaml(src: str) -> dict[str, Any]:
    """Parse the YAML subset that TARS frontmatter uses.

    Supports:
      * key: scalar                 (scalar is str, int, bool, null, or quoted str)
      * key:
          - item1
          - item2                    (block list of scalars)
      * key: [a, b, c]               (flow list of scalars)
      * nested one level:
          key:
            subkey: value
    """
    result: dict[str, Any] = {}
    lines = src.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.strip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\s*)([^:\s][^:]*):\s*(.*?)\s*$", raw)
        if not m:
            i += 1
            continue
        indent = len(m.group(1))
        key = m.group(2).strip()
        inline = m.group(3)
        # Only top-level keys land in result; nested keys parsed as a sub-dict.
        if indent > 0:
            i += 1
            continue
        if inline:
            result[key] = _parse_scalar_or_flow(inline)
            i += 1
            continue
        # Value is on following indented lines — block list or block mapping.
        block: list[str] = []
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if not line.strip():
                block.append(line)
                j += 1
                continue
            stripped = line.lstrip()
            if len(line) - len(stripped) == 0:
                break  # new top-level key
            block.append(line)
            j += 1
        block_text = "\n".join(block)
        if re.search(r"^\s*-\s", block_text, re.MULTILINE):
            result[key] = _parse_block_list(block_text)
        elif re.search(r"^\s*[^:\s-]+:\s", block_text, re.MULTILINE):
            result[key] = _parse_nested_mapping(block_text)
        else:
            # Folded/literal scalar — take trimmed content.
            result[key] = block_text.strip()
        i = j
    return result


def _parse_scalar_or_flow(v: str) -> Any:
    v = v.strip()
    if v == "":
        return ""
    # Flow list
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        if not inner.strip():
            return []
        return [_parse_scalar(x.strip()) for x in _split_commas(inner)]
    return _parse_scalar(v)


def _parse_scalar(v: str) -> Any:
    v = v.strip()
    if not v:
        return ""
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    if v.lower() in ("true", "yes"):
        return True
    if v.lower() in ("false", "no"):
        return False
    if v.lower() in ("null", "~", "none"):
        return None
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def _split_commas(s: str) -> list[str]:
    """Split a flow-list body on commas, respecting bracket balance."""
    out = []
    depth = 0
    cur = []
    for ch in s:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def _parse_block_list(block_text: str) -> list[Any]:
    items: list[Any] = []
    for line in block_text.split("\n"):
        m = re.match(r"^\s*-\s*(.*?)\s*$", line)
        if m:
            items.append(_parse_scalar_or_flow(m.group(1)))
    return items


def _parse_nested_mapping(block_text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in block_text.split("\n"):
        m = re.match(r"^\s*([^:\s][^:]*):\s*(.*?)\s*$", line)
        if m:
            result[m.group(1).strip()] = _parse_scalar_or_flow(m.group(2))
    return result


# ---------------------------------------------------------------------------
# Frontmatter serializer
# ---------------------------------------------------------------------------

def serialize_frontmatter(fm: dict[str, Any]) -> str:
    """Render a frontmatter dict back into YAML-compatible text (no leading/trailing ---)."""
    out = io.StringIO()
    for key, value in fm.items():
        out.write(_serialize_pair(key, value, indent=0))
    return out.getvalue().rstrip() + "\n"


def _serialize_pair(key: str, value: Any, indent: int) -> str:
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            return f"{pad}{key}: {{}}\n"
        s = f"{pad}{key}:\n"
        for k, v in value.items():
            s += _serialize_pair(k, v, indent + 2)
        return s
    if isinstance(value, list):
        if not value and indent == 0:
            return f"{pad}{key}: []\n"
        s = f"{pad}{key}:\n"
        for item in value:
            s += f"{pad}  - {_serialize_scalar(item)}\n"
        return s
    return f"{pad}{key}: {_serialize_scalar(value)}\n"


def _serialize_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote if contains reserved chars or leading/trailing space
    if re.search(r"[:\#\n]", s) or s != s.strip():
        return f'"{s}"'
    return s


# ---------------------------------------------------------------------------
# Note read/write
# ---------------------------------------------------------------------------

def read_note_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_note_text(path: Path, text: str, *, backup: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(path, bak)
    path.write_text(text, encoding="utf-8")


def note_payload(text: str) -> dict[str, Any]:
    """Split a note's text into {'frontmatter': ..., 'body': ...} and return both the
    parsed frontmatter dict and the raw body string."""
    fm, body = split_frontmatter(text)
    return {"frontmatter": fm or {}, "body": body, "has_frontmatter": fm is not None}


def build_note_text(frontmatter: dict[str, Any] | None, body: str) -> str:
    if frontmatter:
        return f"---\n{serialize_frontmatter(frontmatter)}---\n{body.lstrip()}"
    return body


# ---------------------------------------------------------------------------
# Error shaping (PRD §26.15-ish — every tool returns a dict)
# ---------------------------------------------------------------------------

def ok(**kwargs: Any) -> dict[str, Any]:
    return {"status": "ok", **kwargs}


def error(reason: str, **kwargs: Any) -> dict[str, Any]:
    return {"status": "error", "reason": reason, **kwargs}


def to_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, default=str)

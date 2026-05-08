"""Shared helpers for tars-vault tool handlers.

Stdlib-only frontmatter parser with graceful fallback. Handles the
subset of YAML that TARS frontmatter actually uses (scalars, lists,
nested mappings one level deep). Full PyYAML is not a dependency.

All tools read/write UTF-8. All file paths are relative to the vault root.
"""
from __future__ import annotations

import io
import json
import os
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


def _is_unexpanded_var(value: str) -> bool:
    return bool(re.search(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", value))


def resolve_vault_strict(
    *,
    env_value: str | None = None,
    cwd: Path | None = None,
    install_record: Path | None = None,
) -> tuple[Path | None, str | None]:
    """Resolve a vault without ever falling back to an arbitrary CWD."""
    raw_env = env_value if env_value is not None else os.environ.get("TARS_VAULT_PATH")
    current = (cwd or Path.cwd()).expanduser()

    if raw_env:
        if _is_unexpanded_var(raw_env):
            return None, (
                f'TARS_VAULT_PATH was passed as the literal string "{raw_env}". '
                "Set it to the real path to your TARS workspace, or run from inside "
                "that workspace."
            )
        env_path = Path(raw_env).expanduser().resolve()
        if (env_path / "_system").is_dir():
            return env_path, None
        return None, (
            f"TARS_VAULT_PATH is set to {env_path}, but that folder is not a "
            "TARS workspace. Run `/welcome` there first, or correct the path."
        )

    if (current / "_system" / "install.yaml").is_file():
        return current.resolve(), None
    if (current / "_system" / "config.md").is_file():
        return current.resolve(), None

    if install_record and install_record.is_dir() and (install_record / "_system").is_dir():
        return install_record.expanduser().resolve(), None

    return None, (
        "TARS does not know which workspace to use. Set TARS_VAULT_PATH to "
        "your workspace folder, or run from inside it."
    )


def read_install_workspace_path(vault: Path) -> str | None:
    """Read workspace_path/vault_path from a vault install record."""
    install = Path(vault) / "_system" / "install.yaml"
    if not install.is_file():
        return None
    try:
        text = install.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    fallback: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^(workspace_path|vault_path)\s*:\s*(.*?)\s*$", line)
        if not m:
            continue
        value = m.group(2).strip().strip('"').strip("'")
        if not value:
            continue
        if m.group(1) == "workspace_path":
            return value
        fallback = value
    return fallback


def verify_install_alignment(vault: str | Path) -> tuple[bool, str | None]:
    """Return whether the vault path matches its install record.

    Missing install records are allowed for first-run scaffolding. A case-only
    difference is treated as aligned to avoid false positives on common macOS
    case-insensitive volumes.
    """
    actual = Path(vault).expanduser().resolve()
    recorded = read_install_workspace_path(actual)
    if not recorded:
        return True, None
    try:
        recorded_real = Path(recorded).expanduser().resolve()
    except (OSError, RuntimeError):
        return True, None
    if recorded_real == actual or str(recorded_real).lower() == str(actual).lower():
        return True, None
    return False, (
        f"This folder ({actual}) does not match the workspace recorded in "
        f"the install record ({recorded_real}). Run `/welcome --relocate` before writing."
    )


def resolve_note_path(vault: Path, file_or_path: str) -> Path:
    """Given a vault root + a note reference, return the absolute note path.

    Accepts:
      * vault-relative path with or without .md extension
      * vault-relative system/config paths with explicit non-md extensions
      * bare filename (resolves to first match under memory/ or journal/)
    """
    vault = Path(vault)
    raw = str(file_or_path)
    candidate = raw
    explicit_suffix = bool(Path(raw).suffix)
    if not explicit_suffix:
        candidate = candidate + ".md"
    p = (vault / candidate).resolve()
    if explicit_suffix and not p.exists() and Path(raw).suffix != ".md":
        alt = (vault / f"{raw}.md").resolve()
        if alt.exists():
            p = alt
    # Must stay inside the vault
    try:
        p.relative_to(vault)
    except ValueError as exc:
        raise ValueError(f"path escapes vault: {file_or_path}") from exc
    return p


_PROTECTED_PREFIXES = ("_system/", "_views/", "archive/")
_PROTECTED_FILES = {"index.md"}


def is_protected_path(vault: Path, path: Path) -> bool:
    try:
        rel = str(path.resolve().relative_to(Path(vault).resolve())).replace("\\", "/")
    except ValueError:
        return True
    return rel in _PROTECTED_FILES or any(rel.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def protected_path_reason(vault: Path, path: Path) -> str:
    try:
        rel = str(path.resolve().relative_to(Path(vault).resolve())).replace("\\", "/")
    except ValueError:
        rel = str(path)
    return f"{rel} is managed by TARS. Use `/welcome`, `/doctor`, or `/maintain` instead of editing it directly."


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


def parse_full_content(blob: str) -> tuple[dict[str, Any], str]:
    """Split a full Markdown document into frontmatter and body."""
    fm, body = split_frontmatter(blob)
    return fm or {}, body


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
        elif re.search(r"^\s+[^-\s][^:]*:\s", block_text, re.MULTILINE):
            # Indented `key: value` line whose key starts with a non-dash char.
            # The leading `\s+` ensures we're inside a nested block; `[^-\s]`
            # rejects list-item dashes; subsequent `[^:]*` allows hyphens
            # inside identifiers like `tars-bluf-level`.
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

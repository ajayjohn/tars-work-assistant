"""resolve_capability — Return the preferred + fallback MCP servers for a capability.

Reads:
  * _system/integrations.md   (user preference map, YAML inside a fenced block)
  * _system/tools-registry.yaml (auto-discovered live state)

For a capability (e.g. "calendar"), walks the user's preferred list in order,
returning the first server whose discovered state says `status: connected`.
Falls back to declared-but-unverified preferences. Indicates "unresolved" if
no server covers the capability.

Arguments:
  vault:      required.
  capability: required. e.g. "calendar", "tasks", "office-docs".

Returns:
  {status: ok, capability, server, tools, source}
  {status: unresolved, capability, preferred, reason}
  {status: error, reason}
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .. import _common


def _read_preferences(vault: Path) -> dict[str, list[str]]:
    """Extract `capabilities:` block from _system/integrations.md."""
    path = vault / "_system" / "integrations.md"
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    # Find the ```yaml block containing capabilities:
    m = re.search(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        return {}
    yaml_text = m.group(1)
    # Extract `capability: { preferred: [a, b], ...}` lines
    prefs: dict[str, list[str]] = {}
    cap_re = re.compile(
        r"^\s*([a-z][a-z0-9\-]*):\s*\{\s*preferred:\s*\[([^\]]*)\]",
        re.MULTILINE,
    )
    for match in cap_re.finditer(yaml_text):
        name = match.group(1)
        servers = [
            s.strip().strip('"').strip("'")
            for s in match.group(2).split(",")
            if s.strip()
        ]
        prefs[name] = servers
    return prefs


def _read_registry(vault: Path) -> dict[str, dict]:
    """Extract server entries from _system/tools-registry.yaml."""
    path = vault / "_system" / "tools-registry.yaml"
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    # Narrow parser: look for `mcp_servers:` mapping, each entry is a
    # server name followed by an indented block with `status:` / `tools:` etc.
    out: dict[str, dict] = {}
    # Find the section after `mcp_servers:` up to the next top-level key.
    m = re.search(r"^mcp_servers:\s*\n(.*?)^(?=[a-z]|\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}
    body = m.group(1)
    # Split on top-level indented server names (2-space indent)
    server_re = re.compile(r"^  ([a-z][a-z0-9\-]*):\s*$", re.MULTILINE)
    indices = [m2.start() for m2 in server_re.finditer(body)]
    indices.append(len(body))
    for i in range(len(indices) - 1):
        block = body[indices[i]:indices[i + 1]]
        nm = server_re.match(block)
        if not nm:
            continue
        server_name = nm.group(1)
        entry: dict[str, Any] = {}
        status_match = re.search(r"^\s+status:\s*(\S+)\s*$", block, re.MULTILINE)
        if status_match:
            entry["status"] = status_match.group(1)
        tools = [
            t.strip()
            for t in re.findall(r"-\s*\{?name:\s*([^,\}\s]+)", block)
        ]
        entry["tools"] = tools
        caps = re.findall(
            r"capabilities_provided:\s*\[([^\]]+)\]", block
        )
        if caps:
            entry["capabilities_provided"] = [
                c.strip() for c in caps[0].split(",") if c.strip()
            ]
        out[server_name] = entry
    return out


def resolve_capability(**kwargs: Any) -> dict:
    vault = kwargs.get("vault")
    capability = kwargs.get("capability")
    if not vault:
        return _common.error("missing 'vault'")
    if not capability:
        return _common.error("missing 'capability'")
    try:
        vault_p = _common.resolve_vault_path(vault)
    except ValueError as exc:
        return _common.error(str(exc))

    prefs = _read_preferences(vault_p)
    registry = _read_registry(vault_p)
    preferred = prefs.get(capability, [])
    if not preferred:
        return {
            "status": "unresolved",
            "capability": capability,
            "preferred": [],
            "reason": f"no preferences declared for capability {capability!r}",
        }

    # Pass 1 — prefer a server whose registry status is 'connected'.
    for server in preferred:
        meta = registry.get(server)
        if meta and meta.get("status") == "connected":
            return _common.ok(
                capability=capability,
                server=server,
                tools=meta.get("tools", []),
                source="registry:connected",
            )

    # Pass 2 — fall back to any preferred server that is declared in registry.
    for server in preferred:
        if server in registry:
            return _common.ok(
                capability=capability,
                server=server,
                tools=registry[server].get("tools", []),
                source=f"registry:{registry[server].get('status', 'declared')}",
            )

    # Pass 3 — return the first preferred even if not in registry.
    return {
        "status": "unresolved",
        "capability": capability,
        "preferred": preferred,
        "reason": "no preferred server is in tools-registry.yaml — run refresh_integrations",
    }

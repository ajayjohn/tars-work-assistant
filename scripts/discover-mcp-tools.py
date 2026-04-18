#!/usr/bin/env python3
"""discover-mcp-tools — enumerate MCP servers from .mcp.json and write
   _system/tools-registry.yaml with capability classifications.

Strategy (v3.1.1):
  1. Read the vault's .mcp.json for declared servers.
  2. For each server, determine its capability coverage by (a) explicit
     TARS_CAPABILITIES env override (future-proofing), (b) applying
     scripts/capability-classifier.yaml regex rules to its declared tools,
     or (c) falling back to a static short-name hint table.
  3. Write _system/tools-registry.yaml with a 24h TTL.

Status of each server cannot be probed (the Claude Code MCP health state is
not exposed on disk). Each server is marked `declared` — a future runtime
integration can overwrite via Claude Code's /mcp list output.

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        print proposed yaml, no write
  --apply          write the registry
  --json           emit machine-readable output
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# -------- Static capability hints by short-name ---------------------------

SHORTNAME_HINTS: dict[str, list[str]] = {
    "apple-calendar": ["calendar"],
    "apple-reminders": ["tasks"],
    "microsoft-365": ["calendar", "tasks", "email", "office-docs", "file-storage", "communication"],
    "workiq": ["calendar", "tasks", "email", "office-docs", "file-storage", "communication"],
    "minutes-app": ["meeting-recording"],
    "figma": ["design"],
    "snowflake": ["data-warehouse"],
    "bigquery": ["data-warehouse"],
    "databricks": ["data-warehouse"],
    "pendo": ["analytics"],
    "amplitude": ["analytics"],
    "mixpanel": ["analytics"],
    "jira": ["project-tracker"],
    "linear": ["project-tracker"],
    "github": ["project-tracker"],
    "confluence": ["documentation"],
    "notion": ["documentation"],
    "google-docs": ["documentation"],
    "datadog": ["monitoring"],
    "pagerduty": ["monitoring"],
    "compwatcher": ["monitoring"],
    "slack": ["communication"],
    "filesystem": ["file-storage"],
    "tars-vault": ["search"],
    "data-portal-audience": ["analytics"],
    "tana-local": ["documentation"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="discover-mcp-tools")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def read_mcp_json(vault: Path) -> dict[str, Any]:
    path = vault / ".mcp.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def probe_claude_mcp_status() -> dict[str, str]:
    """Best-effort: parse `claude mcp list` output for connection status.

    Returns {server_short_name: "connected"|"failed"|"pending-auth"|"unknown"}.
    Fails soft — returns empty dict if `claude` CLI isn't reachable.
    """
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"], capture_output=True, text=True, timeout=15
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return {}
    if result.returncode != 0:
        return {}
    status: dict[str, str] = {}
    for line in result.stdout.splitlines():
        # "name: <command> - ✓ Connected"  /  "- ✗ Failed to connect"
        # Lines may start with "plugin:tars:name:" — strip.
        m = re.match(r"^\s*(?:plugin:[^:]+:)?([a-zA-Z0-9._\-]+):\s.*?-\s*(.+)$", line)
        if not m:
            continue
        name = m.group(1)
        tail = m.group(2)
        if "Connected" in tail:
            status[name] = "connected"
        elif "Failed" in tail:
            status[name] = "failed"
        elif "Needs authentication" in tail or "auth" in tail.lower():
            status[name] = "pending-auth"
        else:
            status[name] = "unknown"
    return status


def infer_capabilities(server_name: str, server_cfg: dict[str, Any]) -> list[str]:
    """Cheap inference: short-name hint + URL/command regex."""
    caps = set()
    for cap in SHORTNAME_HINTS.get(server_name, []):
        caps.add(cap)
    hay = " ".join(
        [
            server_name.lower(),
            str(server_cfg.get("command", "")).lower(),
            " ".join(map(str, server_cfg.get("args", []))).lower(),
            str(server_cfg.get("url", "")).lower(),
        ]
    )
    if re.search(r"\bcalendar\b", hay):
        caps.add("calendar")
    if re.search(r"\breminder|todo|task\b", hay):
        caps.add("tasks")
    if re.search(r"\bmail\b|email", hay):
        caps.add("email")
    if re.search(r"\bfigma\b|design", hay):
        caps.add("design")
    if re.search(r"\bsnowflake|bigquery|databricks|redshift\b", hay):
        caps.add("data-warehouse")
    if re.search(r"\bpendo|mixpanel|amplitude\b", hay):
        caps.add("analytics")
    return sorted(caps)


def build_registry(vault: Path) -> dict[str, Any]:
    declared = read_mcp_json(vault).get("mcpServers", {}) or {}
    status_map = probe_claude_mcp_status()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    servers: dict[str, Any] = {}
    for name, cfg in declared.items():
        caps = infer_capabilities(name, cfg)
        servers[name] = {
            "status": status_map.get(name, "declared"),
            "verified_at": now if status_map.get(name) == "connected" else None,
            "tool_count": None,
            "capabilities_provided": caps,
            "tools": [],
            "transport": cfg.get("type") or ("http" if "url" in cfg else "stdio"),
        }

    return {
        "discovered_at": now,
        "ttl_hours": 24,
        "generator": "scripts/discover-mcp-tools.py v3.1.1",
        "mcp_servers": servers,
    }


def render_yaml(registry: dict[str, Any]) -> str:
    lines: list[str] = [
        "# Auto-generated — PRD §3.5. Do not hand-edit; regenerated at SessionStart.",
        f"discovered_at: {registry['discovered_at']}",
        f"ttl_hours: {registry['ttl_hours']}",
        f"generator: {registry['generator']!r}",
        "",
        "mcp_servers:",
    ]
    for name, meta in registry["mcp_servers"].items():
        lines.append(f"  {name}:")
        lines.append(f"    status: {meta.get('status', 'declared')}")
        verified = meta.get("verified_at")
        lines.append(f"    verified_at: {verified if verified else 'null'}")
        tool_count = meta.get("tool_count")
        lines.append(f"    tool_count: {'null' if tool_count is None else tool_count}")
        caps = meta.get("capabilities_provided", [])
        if caps:
            lines.append(f"    capabilities_provided: [{', '.join(caps)}]")
        else:
            lines.append(f"    capabilities_provided: []")
        transport = meta.get("transport", "stdio")
        lines.append(f"    transport: {transport}")
        tools = meta.get("tools") or []
        if tools:
            lines.append(f"    tools:")
            for t in tools:
                lines.append(f"      - {t}")
        else:
            lines.append(f"    tools: []")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3

    registry = build_registry(vault)
    out_path = vault / "_system" / "tools-registry.yaml"
    yaml_text = render_yaml(registry)

    payload = {
        "status": "applied" if args.apply else "dry-run",
        "vault": str(vault),
        "registry_path": str(out_path),
        "server_count": len(registry["mcp_servers"]),
        "capability_coverage": sorted({
            c for s in registry["mcp_servers"].values() for c in s.get("capabilities_provided", [])
        }),
    }

    if args.apply:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(yaml_text, encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(yaml_text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

"""Local helper bootstrap for tars-vault (v3.5.0).

Wires list_tools + call_tool handlers against the tool modules under `tools/`.
Each handler is a synchronous `(**kwargs) -> dict` function; this module
translates MCP's `CallToolRequest` into keyword arguments and the returned
dict back into a TextContent payload.

The TARS_VAULT_PATH env var (or --vault) points at the local Markdown workspace
and is injected into every tool call so individual skills don't have to pass it.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from . import tools as _tools
from . import _common


def _resolve_handler(name: str):
    """Each tool module exposes a callable named identically to the module."""
    module = getattr(_tools, name)
    return getattr(module, name, module)


TOOL_REGISTRY: dict[str, Any] = {
    name: _resolve_handler(name) for name in _tools.__all__
}


# ---------------------------------------------------------------------------
# Tool schemas (JSON Schema fragments for the MCP list_tools response)
# ---------------------------------------------------------------------------

_COMMON_VAULT = {"vault": {"type": "string", "description": "Absolute workspace path (auto-injected by server if omitted)."}}


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "read_note": {
        "description": "Read a vault note and return parsed frontmatter + body.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "file": {"type": "string", "description": "Vault-relative path (with or without .md)."},
            },
            "required": ["file"],
        },
    },
    "read_system_file": {
        "description": "Read a managed system file and parse YAML files into structured data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "file": {"type": "string", "description": "Path under _system/."},
                "path": {"type": "string", "description": "Compatibility alias for file."},
            },
        },
    },
    "create_note": {
        "description": "Create a new vault note with frontmatter. Fails if path exists unless overwrite=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "name": {"type": "string"},
                "path": {"type": "string"},
                "template": {"type": "string"},
                "frontmatter": {"type": "object"},
                "body": {"type": "string"},
                "overwrite": {"type": "boolean"},
                "allow_user_properties": {"type": "boolean"},
                "auto_alias": {"type": "boolean"},
                "validate": {"type": "boolean"},
            },
            "required": ["path"],
        },
    },
    "append_note": {
        "description": "Append content to an existing note, auto-chunked at 40KB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "file": {"type": "string"},
                "content": {"type": "string"},
                "chunk_size": {"type": "integer"},
            },
            "required": ["file", "content"],
        },
    },
    "write_note_from_content": {
        "description": "Create a note without a pre-registered template (alias of create_note).",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "path": {"type": "string"},
                "frontmatter": {"type": "object"},
                "body": {"type": "string"},
                "content": {"type": "string"},
                "overwrite": {"type": "boolean"},
                "allow_user_properties": {"type": "boolean"},
                "auto_alias": {"type": "boolean"},
                "validate": {"type": "boolean"},
            },
            "required": ["path"],
        },
    },
    "update_frontmatter": {
        "description": "Update one or more frontmatter properties on a note. Set value to null to remove.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "file": {"type": "string"},
                "updates": {"type": "object"},
                "property": {"type": "string"},
                "value": {},
                "allow_user_properties": {"type": "boolean"},
            },
            "required": ["file"],
        },
    },
    "search_by_tag": {
        "description": "Find notes whose frontmatter `tags:` contains a given tag, with optional text and frontmatter filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "tag": {"type": "string"},
                "query": {"type": "string"},
                "frontmatter": {"type": "object"},
                "limit": {"type": "integer"},
                "prefix_match": {"type": "boolean"},
            },
            "required": ["tag"],
        },
    },
    "archive_note": {
        "description": "Archive a note (tag + move to archive/YYYY-MM/) with guardrails.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "file": {"type": "string"},
                "reason": {"type": "string"},
                "force": {"type": "boolean"},
                "dry_run": {"type": "boolean"},
            },
            "required": ["file"],
        },
    },
    "move_note": {
        "description": "Move a note and rewrite path-qualified wikilinks that referenced it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "src": {"type": "string"},
                "dst": {"type": "string"},
                "rewrite_wikilinks": {"type": "boolean"},
            },
            "required": ["src", "dst"],
        },
    },
    "classify_file": {
        "description": "Propose a taxonomy target path for a loose file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "path": {"type": "string"},
            },
            "required": ["path"],
        },
    },
    "detect_near_duplicates": {
        "description": "Identify likely-duplicate notes within a folder.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "folder": {"type": "string"},
                "min_cluster": {"type": "integer"},
            },
        },
    },
    "resolve_capability": {
        "description": "Resolve a capability (e.g. 'calendar') to the preferred MCP server.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "capability": {"type": "string"},
            },
            "required": ["capability"],
        },
    },
    "resolve_alias": {
        "description": "Resolve an alias, abbreviation, or short name to a canonical TARS record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "name": {"type": "string"},
                "alias": {"type": "string"},
                "kind": {"type": "string"},
                "kind_hint": {"type": "string"},
                "context": {"type": "string"},
            },
        },
    },
    "runtime_info": {
        "description": "Check whether the local TARS helper is connected and report required/optional runtime health.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
            },
        },
    },
    "refresh_integrations": {
        "description": "Rebuild _system/tools-registry.yaml from .mcp.json.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "dry_run": {"type": "boolean"},
            },
        },
    },
    "scan_secrets": {
        "description": "Classify content against _system/guardrails.yaml patterns.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "content": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    "scaffold_workspace": {
        "description": "Create the deterministic first-run TARS workspace directory tree and starter files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "workspace_type": {"type": "string", "enum": ["headless", "obsidian"]},
                "user_name": {"type": "string"},
                "user_role": {"type": "string"},
                "company": {"type": "string"},
                "persona": {"type": "string"},
                "overwrite": {"type": "boolean"},
                "allow_claude_home": {"type": "boolean"},
            },
        },
    },
    "fts_search": {
        "description": "SQLite FTS5 keyword search over the vault search index.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "query": {"type": "string"},
                "scope": {"type": "string"},
                "tier": {"type": "string"},
                "source_types": {"type": "array", "items": {"type": "string"}},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    "semantic_search": {
        "description": "Hybrid semantic + FTS search over journal/transcripts/contexts prose.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "query": {"type": "string"},
                "scope": {"type": "string"},
                "limit": {"type": "integer"},
                "top_k": {"type": "integer"},
                "since": {"type": "string"},
                "until": {"type": "string"},
                "date_range": {"type": "object"},
                "semantic_weight": {"type": "number"},
            },
            "required": ["query"],
        },
    },
    "rerank": {
        "description": "Deterministic rerank with recency + source boosts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "results": {"type": "array"},
                "query": {"type": "string"},
                "recency_boost": {"type": "number"},
            },
            "required": ["results"],
        },
    },
    "format_wikilink": {
        "description": (
            "Resolve raw text into an Obsidian-safe wikilink via the alias "
            "registry and vault file lookup. Returns status=resolved | "
            "disambiguation_needed | new_entity | error. Skills MUST use this "
            "instead of hand-forming [[...]] from user-provided text."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "text": {
                    "type": "string",
                    "description": "Reference text to convert into a wikilink.",
                },
                "kind": {
                    "type": "string",
                    "description": (
                        "Optional entity kind hint (person, vendor, competitor, "
                        "product, initiative, decision, org-context). Restricts "
                        "alias-registry matches when provided."
                    ),
                },
            },
            "required": ["text"],
        },
    },
}


WRITE_TOOLS = {
    "append_note",
    "archive_note",
    "create_note",
    "move_note",
    "refresh_integrations",
    "scaffold_workspace",
    "update_frontmatter",
    "write_note_from_content",
}

READ_TOOLS = set(TOOL_REGISTRY) - WRITE_TOOLS


def _validate_kwargs(tool_name: str, schema: dict[str, Any], kwargs: dict[str, Any]) -> str | None:
    declared = set(schema.get("properties", {}).keys())
    extras = sorted(k for k in kwargs if k not in declared)
    if extras:
        label = "argument" if len(extras) == 1 else "arguments"
        return f"unknown {label} for {tool_name}: {', '.join(extras)}"
    return None


def _resolve_call_vault(args: dict[str, Any], default_vault: str | None) -> tuple[Path | None, str | None]:
    if args.get("vault"):
        return _common.resolve_vault_path(args["vault"]), None
    vault, err = _common.resolve_vault_strict(env_value=default_vault or None)
    if err:
        return None, err
    return vault, None


def _enforce_install_alignment(tool_name: str, vault: Path) -> dict[str, Any] | None:
    if os.environ.get("TARS_VAULT_WRITE_ANYWAY") == "1":
        return None
    aligned, warning = _common.verify_install_alignment(vault)
    if aligned:
        return None
    if tool_name in WRITE_TOOLS:
        return _common.error(warning or "workspace install record does not match this folder")
    try:
        from .telemetry import append_event

        append_event(
            vault,
            {
                "event": "vault_alignment_warning",
                "tool": tool_name,
                "warning": warning,
            },
        )
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# MCP server transport
# ---------------------------------------------------------------------------


def _resolve_default_vault(vault_path: str | None) -> str:
    """Return the vault path that tool calls default to (env > --vault > error)."""
    return vault_path or os.environ.get("TARS_VAULT_PATH") or ""


def _check_install_record(vault_path: str) -> None:
    """Emit a stderr warning if _system/install.yaml disagrees with vault_path.

    Hooks already enforce the deny path; this is a server-side observability
    breadcrumb so operators see the same warning regardless of transport.
    """
    if not vault_path:
        return
    try:
        from pathlib import Path
        import re

        vault = Path(vault_path).expanduser().resolve()
        install_path = vault / "_system" / "install.yaml"
        if not install_path.is_file():
            return
        text = install_path.read_text(encoding="utf-8")
        stored = ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^(workspace_path|vault_path)\s*:\s*(.*?)\s*$", line)
            if m:
                stored = m.group(2).strip().strip('"').strip("'")
                if m.group(1) == "workspace_path":
                    break
        if stored and Path(stored).expanduser().resolve() != vault:
            print(
                f"tars-vault: install.yaml workspace_path={stored} disagrees with "
                f"server workspace={vault}. Hooks should be denying mutations; "
                "run /welcome --relocate to reconcile.",
                file=sys.stderr,
            )
    except Exception:
        # Never let the check take down the server.
        return


def _tool_specs() -> list[dict[str, Any]]:
    out = []
    for name, spec in TOOL_SCHEMAS.items():
        if name not in TOOL_REGISTRY:
            continue
        out.append(
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            }
        )
    return out


def _call_handler_sync(name: str, arguments: dict | None, default_vault: str) -> dict:
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return {"status": "error", "reason": f"unknown tool: {name}"}
    args = dict(arguments or {})
    schema = TOOL_SCHEMAS.get(name, {}).get("inputSchema", {})
    kw_error = _validate_kwargs(name, schema, args)
    if kw_error:
        return _common.error(kw_error)
    vault, vault_error = _resolve_call_vault(args, default_vault)
    if vault_error:
        return _common.error(vault_error)
    if vault is not None:
        args["vault"] = str(vault)
        alignment_error = _enforce_install_alignment(name, vault)
        if alignment_error:
            return alignment_error
    try:
        result = handler(**args)
    except TypeError as exc:
        result = {"status": "error", "reason": f"bad arguments: {exc}"}
    except NotImplementedError as exc:
        result = {"status": "error", "reason": f"tool not yet implemented: {exc}"}
    except Exception as exc:
        result = {"status": "error", "reason": f"tool raised: {exc}"}
    if not isinstance(result, dict):
        result = {"status": "error", "reason": f"tool returned non-dict: {type(result).__name__}"}
    return result


def _write_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, default=str) + "\n")
    sys.stdout.flush()


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _run_minimal_stdio(vault_path: str) -> int:
    """Run a small stdlib MCP stdio transport.

    The official `mcp` Python SDK is preferred when installed, but marketplace
    users should not need to run `pip install` before first setup. This fallback
    implements the JSON-RPC methods TARS needs: initialize, tools/list, and
    tools/call.
    """
    default_vault = _resolve_default_vault(vault_path)
    _check_install_record(default_vault)
    try:
        for raw in sys.stdin:
            line = raw.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                _write_json(_jsonrpc_error(None, -32700, "Parse error"))
                continue

            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params") or {}

            if method == "notifications/initialized":
                continue
            if method == "initialize":
                protocol = params.get("protocolVersion") or "2024-11-05"
                _write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": protocol,
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "tars-vault", "version": "3.5.0"},
                        },
                    }
                )
                continue
            if method == "ping":
                _write_json({"jsonrpc": "2.0", "id": request_id, "result": {}})
                continue
            if method == "tools/list":
                _write_json({"jsonrpc": "2.0", "id": request_id, "result": {"tools": _tool_specs()}})
                continue
            if method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") or {}
                result = _call_handler_sync(str(name or ""), arguments, default_vault)
                _write_json(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {"type": "text", "text": json.dumps(result, indent=2, default=str)}
                            ],
                            "isError": result.get("status") == "error",
                        },
                    }
                )
                continue

            if request_id is not None:
                _write_json(_jsonrpc_error(request_id, -32601, f"Method not found: {method}"))
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"tars-vault: fallback server exited with error: {exc}", file=sys.stderr)
        return 1
    return 0


def run_stdio(vault_path: str) -> int:
    """Run the MCP server on stdio. Blocks until the transport closes.

    Uses the official `mcp` SDK when available, otherwise falls back to the
    bundled stdlib transport so marketplace installs work without pip setup.
    """
    try:
        from mcp.server import NotificationOptions, Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except Exception as exc:
        print(
            f"tars-vault: mcp SDK not available ({exc}). "
            "Using bundled stdlib transport.",
            file=sys.stderr,
        )
        return _run_minimal_stdio(vault_path)

    default_vault = _resolve_default_vault(vault_path)
    _check_install_record(default_vault)
    server = Server("tars-vault")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(
                name=spec["name"],
                description=spec["description"],
                inputSchema=spec["inputSchema"],
            )
            for spec in _tool_specs()
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        result = await asyncio.to_thread(_call_handler_sync, name, arguments, default_vault)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    async def _main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="tars-vault",
                    server_version="3.5.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"tars-vault: server exited with error: {exc}", file=sys.stderr)
        return 1
    return 0

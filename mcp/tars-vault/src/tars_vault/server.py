"""MCP server bootstrap for tars-vault (v3.1.1).

Wires list_tools + call_tool handlers against the tool modules under `tools/`.
Each handler is a synchronous `(**kwargs) -> dict` function; this module
translates MCP's `CallToolRequest` into keyword arguments and the returned
dict back into a TextContent payload.

The TARS_VAULT_PATH env var (or --vault) is injected into every tool call so
individual skills don't have to pass it explicitly.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from . import tools as _tools


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

_COMMON_VAULT = {"vault": {"type": "string", "description": "Absolute vault path (auto-injected by server if omitted)."}}


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
    "create_note": {
        "description": "Create a new vault note with frontmatter. Fails if path exists unless overwrite=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "path": {"type": "string"},
                "frontmatter": {"type": "object"},
                "body": {"type": "string"},
                "overwrite": {"type": "boolean"},
                "allow_user_properties": {"type": "boolean"},
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
                "overwrite": {"type": "boolean"},
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
                "allow_user_properties": {"type": "boolean"},
            },
            "required": ["file", "updates"],
        },
    },
    "search_by_tag": {
        "description": "Find notes whose frontmatter `tags:` contains a given tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_COMMON_VAULT,
                "tag": {"type": "string"},
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
                "since": {"type": "string"},
                "until": {"type": "string"},
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
}


# ---------------------------------------------------------------------------
# MCP server — wired against the mcp SDK
# ---------------------------------------------------------------------------


def _resolve_default_vault(vault_path: str | None) -> str:
    """Return the vault path that tool calls default to (env > --vault > error)."""
    return vault_path or os.environ.get("TARS_VAULT_PATH") or ""


def run_stdio(vault_path: str) -> int:
    """Run the MCP server on stdio. Blocks until the transport closes.

    Returns 0 on clean shutdown, 3 if the `mcp` SDK is unavailable.
    """
    try:
        from mcp.server import NotificationOptions, Server
        from mcp.server.models import InitializationOptions
        from mcp.server.stdio import stdio_server
        from mcp.types import Tool, TextContent
    except Exception as exc:
        print(
            f"tars-vault: mcp SDK not available ({exc}). "
            "Install with: pip install 'mcp>=1.0,<2.0'",
            file=sys.stderr,
        )
        return 3

    default_vault = _resolve_default_vault(vault_path)
    server = Server("tars-vault")

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        out = []
        for name, spec in TOOL_SCHEMAS.items():
            if name not in TOOL_REGISTRY:
                continue
            out.append(
                Tool(
                    name=name,
                    description=spec["description"],
                    inputSchema=spec["inputSchema"],
                )
            )
        return out

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        handler = TOOL_REGISTRY.get(name)
        if handler is None:
            payload = {"status": "error", "reason": f"unknown tool: {name}"}
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]
        args = dict(arguments or {})
        if "vault" not in args and default_vault:
            args["vault"] = default_vault
        # Run the synchronous handler off the event loop.
        try:
            result = await asyncio.to_thread(handler, **args)
        except TypeError as exc:
            result = {"status": "error", "reason": f"bad arguments: {exc}"}
        except NotImplementedError as exc:
            result = {"status": "error", "reason": f"tool not yet implemented: {exc}"}
        except Exception as exc:  # defensive: never kill the server
            result = {"status": "error", "reason": f"tool raised: {exc}"}
        if not isinstance(result, dict):
            result = {"status": "error", "reason": f"tool returned non-dict: {type(result).__name__}"}
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    async def _main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="tars-vault",
                    server_version="3.1.1",
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

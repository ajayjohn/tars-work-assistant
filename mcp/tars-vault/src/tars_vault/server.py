"""MCP server bootstrap. Skeleton for Phase 1a — tools are registered by name
with placeholder handlers. Full implementations land in later phases.
"""
import sys
from typing import Any

from . import tools


TOOL_REGISTRY: dict[str, Any] = {
    name: getattr(tools, name) for name in tools.__all__
}


def run_stdio(vault_path: str) -> int:
    """Run the MCP server on stdio.

    Skeleton behaviour: import the `mcp` SDK when available. If the SDK is not
    installed, print a clear error and exit non-zero so the caller knows the
    runtime is incomplete.
    """
    try:
        from mcp.server import Server  # type: ignore
        from mcp.server.stdio import stdio_server  # type: ignore
    except Exception as exc:  # pragma: no cover — SDK not installed in this env
        print(
            f"tars-vault: mcp SDK not available ({exc}). "
            "Install with: pip install 'mcp>=1.0,<2.0'",
            file=sys.stderr,
        )
        return 3

    server = Server("tars-vault")
    # Tool registration happens in later phases; for the skeleton we only prove
    # the server can boot and advertise its identity.
    _ = (server, stdio_server, vault_path, TOOL_REGISTRY)
    return 0

#!/usr/bin/env python3
"""Validate the built TARS plugin artifact, not just repo source files."""
from __future__ import annotations

import argparse
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


REQUIRED_FILES = {
    ".claude-plugin/plugin.json",
    ".claude-plugin/mcp-servers.json",
    ".mcp.json",
    "commands/welcome.md",
    "commands/doctor.md",
    "skills/welcome/SKILL.md",
    "skills/doctor/SKILL.md",
    "CLAUDE.md",
    "mcp/tars-vault/src/tars_vault/tools/scaffold_workspace.py",
    "mcp/tars-vault/src/tars_vault/tools/runtime_info.py",
    "mcp/tars-vault/src/tars_vault/tools/resolve_alias.py",
    "requirements.txt",
    "requirements-search.txt",
}

REQUIRED_TOOLS = {
    "append_note",
    "archive_candidates",
    "archive_note",
    "classify_file",
    "context_bundle",
    "context_gaps",
    "create_note",
    "detect_near_duplicates",
    "entity_timeline",
    "format_wikilink",
    "fts_search",
    "move_note",
    "read_note",
    "read_system_file",
    "refresh_integrations",
    "rerank",
    "resolve_alias",
    "resolve_capability",
    "runtime_info",
    "scan_secrets",
    "scaffold_workspace",
    "search_by_tag",
    "semantic_search",
    "update_frontmatter",
    "workspace_map",
    "write_note_from_content",
}

FORBIDDEN_ROOT_PATHS = {
    "_system/",
    "_views/",
    "knowledge/",
    "projects/",
    "research/",
}

STALE_TEXT = {
    "Obsidian-native",
    "You operate on an Obsidian vault",
    "obsidian-cli available",
    "obsidian-cli installed",
    "/tars:",
}

CANONICAL_DIRS = {
    "_system",
    "memory",
    "journal",
    "contexts",
    "inbox/pending",
    "inbox/processed",
    "archive",
    "templates",
    "scripts",
}

GENERIC_DIRS = {"knowledge", "projects", "research"}
FORBIDDEN_WORKSPACE_FILES = {"INBOX.md", "MEMORY.md", "PEOPLE.md", "INITIATIVES.md", "inbox.md"}


def pass_(message: str) -> None:
    print(f"PASS  {message}")


def fail(message: str) -> None:
    print(f"FAIL  {message}")
    raise SystemExit(1)


def validate_zip_members(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    missing = sorted(REQUIRED_FILES - names)
    if missing:
        fail(f"artifact missing required files: {missing}")
    pass_("artifact includes commands, welcome skill, doctor skill, CLAUDE.md, helper metadata, and required helper tools")

    forbidden = sorted(path for path in FORBIDDEN_ROOT_PATHS if path in names)
    if forbidden:
        fail(f"artifact includes runtime workspace paths at package root: {forbidden}")
    pass_("artifact does not ship a fake runtime workspace")


def _server_spec_from_manifest(root: Path) -> dict:
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    inline = plugin.get("mcpServers", {})
    if "tars-vault" not in inline:
        fail("packaged plugin.json missing inline mcpServers.tars-vault")
    root_mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
    if "mcpServers" not in root_mcp:
        fail("packaged root .mcp.json must use standard mcpServers shape")
    if "tars-vault" not in root_mcp["mcpServers"]:
        fail("packaged root .mcp.json missing tars-vault")
    root_servers = root_mcp["mcpServers"]
    for label, spec in (("plugin.json", inline["tars-vault"]), (".mcp.json", root_servers["tars-vault"])):
        env = spec.get("env", {})
        py_path = env.get("PYTHONPATH", "")
        if "${CLAUDE_PLUGIN_ROOT}" not in py_path:
            fail(f"{label} tars-vault PYTHONPATH must use CLAUDE_PLUGIN_ROOT")
    pass_("packaged manifests declare tars-vault in plugin.json and root .mcp.json")
    return inline["tars-vault"]


def validate_text_surface(root: Path) -> None:
    checked = [
        root / "CLAUDE.md",
        root / "README.md",
        root / "commands" / "welcome.md",
        root / "skills" / "welcome" / "SKILL.md",
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "mcp-servers.json",
        root / ".mcp.json",
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8")
        hits = [needle for needle in STALE_TEXT if needle in text]
        if hits:
            fail(f"{path.relative_to(root)} contains stale install language: {hits}")
    welcome_command = (root / "commands" / "welcome.md").read_text(encoding="utf-8")
    for needle in (
        "from the user's workspace",
        "Natural-language example",
        "Paste or upload a meeting transcript",
        "Do not recommend `/briefing` as a starter action",
    ):
        if needle not in welcome_command:
            fail(f"commands/welcome.md missing fallback guard: {needle}")
    pass_("packaged user surface avoids stale Obsidian-required and /tars:* language")


def validate_tool_registry_from_artifact(root: Path) -> None:
    sys.path.insert(0, str(root / "mcp" / "tars-vault" / "src"))
    try:
        from tars_vault import server
    finally:
        try:
            sys.path.remove(str(root / "mcp" / "tars-vault" / "src"))
        except ValueError:
            pass

    schema_tools = set(server.TOOL_SCHEMAS)
    registry_tools = set(server.TOOL_REGISTRY)
    missing = sorted(REQUIRED_TOOLS - schema_tools)
    if missing:
        fail(f"server schema missing required tools: {missing}")
    missing_registry = sorted(REQUIRED_TOOLS - registry_tools)
    if missing_registry:
        fail(f"server registry missing required tools: {missing_registry}")
    pass_("artifact server registry exposes required TARS helper tools")


def _read_json_response(proc: subprocess.Popen[str], expected_id: int, timeout: float) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            fail(f"helper exited before response id {expected_id}: {stderr.strip()}")
        ready, _, _ = select.select([proc.stdout], [], [], max(0.0, deadline - time.time()))
        if not ready:
            continue
        line = proc.stdout.readline()
        if not line:
            continue
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("id") == expected_id:
            if "error" in payload:
                fail(f"helper response id {expected_id} returned error: {payload['error']}")
            return payload
    stderr = proc.stderr.read() if proc.stderr else ""
    fail(f"timed out waiting for helper response id {expected_id}: {stderr.strip()}")
    return {}


def validate_runtime_list_tools(root: Path) -> None:
    spec = _server_spec_from_manifest(root)
    args = [sys.executable if spec["command"] == "python3" else spec["command"], *spec["args"]]
    workspace = Path(tempfile.mkdtemp(prefix="tars-runtime-workspace-"))
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(root)
    env["TARS_VAULT_PATH"] = str(workspace)
    for key, value in spec.get("env", {}).items():
        env[key] = (
            value.replace("${CLAUDE_PLUGIN_ROOT}", str(root))
            .replace("${TARS_VAULT_PATH}", str(workspace))
        )

    proc = subprocess.Popen(
        args,
        cwd=str(root),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdin is not None
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tars-artifact-validator", "version": "0"},
            },
        }
        proc.stdin.write(json.dumps(init) + "\n")
        proc.stdin.flush()
        _read_json_response(proc, 1, timeout=10)

        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n")
        proc.stdin.flush()
        response = _read_json_response(proc, 2, timeout=10)
        tools = {
            tool["name"]
            for tool in response.get("result", {}).get("tools", [])
            if isinstance(tool, dict) and "name" in tool
        }
        missing = sorted(REQUIRED_TOOLS - tools)
        if missing:
            fail(f"runtime list_tools missing required tools: {missing}")
        pass_("packaged local TARS helper starts over stdio and lists required tools")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(workspace, ignore_errors=True)


def run_scaffold_from_artifact(root: Path, workspace_type: str) -> Path:
    sys.path.insert(0, str(root / "mcp" / "tars-vault" / "src"))
    from tars_vault.tools.scaffold_workspace import scaffold_workspace

    workspace_parent = Path(tempfile.mkdtemp(prefix=f"tars-artifact-{workspace_type}-"))
    workspace = workspace_parent / "TARS Workspace"
    result = scaffold_workspace(
        vault=str(workspace),
        workspace_type=workspace_type,
        user_name="Taylor",
        user_role="Product Leader",
        company="Acme",
        persona="product-leader",
    )
    if result.get("status") != "ok":
        fail(f"{workspace_type} scaffold failed: {result}")
    return workspace


def validate_workspace(workspace: Path, *, obsidian: bool) -> None:
    for rel in CANONICAL_DIRS:
        if not (workspace / rel).is_dir():
            fail(f"missing canonical workspace directory: {rel}")
    for rel in GENERIC_DIRS:
        if (workspace / rel).exists():
            fail(f"generic workspace directory should not exist: {rel}")
    for rel in FORBIDDEN_WORKSPACE_FILES:
        if (workspace / rel).exists():
            fail(f"root inbox/memory index file should not exist: {rel}")

    index = workspace / "index.md"
    install = workspace / "_system" / "install.yaml"
    config = workspace / "_system" / "config.md"
    for path in (index, install, config):
        if not path.is_file():
            fail(f"missing scaffolded file: {path.relative_to(workspace)}")

    text = index.read_text(encoding="utf-8")
    for needle in (
        "Slash commands are optional",
        "Process everything in my inbox",
        "inbox/pending/",
        "Paste a meeting transcript",
        "not a single `INBOX.md` note",
        "Check my TARS install",
    ):
        if needle not in text:
            fail(f"index.md missing first-user guidance: {needle}")

    views = workspace / "_views"
    if obsidian and not (views / "inbox-pending.base").is_file():
        fail("Obsidian scaffold missing _views/inbox-pending.base")
    if not obsidian and views.exists():
        fail("headless scaffold created _views")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", nargs="?", default="tars-cowork-plugin/Archive.zip")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).resolve()
    if not zip_path.is_file():
        fail(f"artifact zip not found: {zip_path}")

    validate_zip_members(zip_path)

    extract_root = Path(tempfile.mkdtemp(prefix="tars-artifact-extract-"))
    workspaces: list[Path] = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_root)

        validate_text_surface(extract_root)
        validate_tool_registry_from_artifact(extract_root)
        validate_runtime_list_tools(extract_root)

        headless = run_scaffold_from_artifact(extract_root, "headless")
        workspaces.append(headless.parent)
        validate_workspace(headless, obsidian=False)
        pass_("installed artifact headless scaffold creates canonical portable workspace")

        obsidian = run_scaffold_from_artifact(extract_root, "obsidian")
        workspaces.append(obsidian.parent)
        validate_workspace(obsidian, obsidian=True)
        pass_("installed artifact Obsidian scaffold uses same workspace plus _views")
    finally:
        shutil.rmtree(extract_root, ignore_errors=True)
        for path in workspaces:
            shutil.rmtree(path, ignore_errors=True)

    print("ALL ARTIFACT CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

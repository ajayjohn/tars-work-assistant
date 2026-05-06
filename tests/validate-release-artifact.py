#!/usr/bin/env python3
"""Validate the built TARS plugin artifact, not just repo source files."""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


REQUIRED_FILES = {
    ".claude-plugin/plugin.json",
    ".claude-plugin/mcp-servers.json",
    "commands/welcome.md",
    "commands/start.md",
    "skills/welcome/SKILL.md",
    "CLAUDE.md",
    "mcp/tars-vault/src/tars_vault/tools/scaffold_workspace.py",
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
    pass_("artifact includes commands, welcome skill, CLAUDE.md, MCP metadata, and scaffold tool")

    forbidden = sorted(path for path in FORBIDDEN_ROOT_PATHS if path in names)
    if forbidden:
        fail(f"artifact includes runtime workspace paths at package root: {forbidden}")
    pass_("artifact does not ship a fake runtime workspace")


def validate_text_surface(root: Path) -> None:
    checked = [
        root / "CLAUDE.md",
        root / "README.md",
        root / "skills" / "welcome" / "SKILL.md",
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "mcp-servers.json",
    ]
    for path in checked:
        text = path.read_text(encoding="utf-8")
        hits = [needle for needle in STALE_TEXT if needle in text]
        if hits:
            fail(f"{path.relative_to(root)} contains stale install language: {hits}")
    pass_("packaged user surface avoids stale Obsidian-required and /tars:* language")


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
        "Paste a transcript",
        "not a single `INBOX.md` note",
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

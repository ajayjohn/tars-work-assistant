#!/usr/bin/env python3
"""Fast framework-wide contract checks for skills, commands, docs, and tools."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcp" / "tars-vault" / "src"))

from tars_vault.server import TOOL_SCHEMAS


FAIL = 0


def pass_(message: str) -> None:
    print(f"PASS  {message}")


def fail(message: str) -> None:
    global FAIL
    FAIL = 1
    print(f"FAIL  {message}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def files_under(*roots: str) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        base = ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}:
                out.append(path)
    return out


def validate_tool_references() -> None:
    tools = set(TOOL_SCHEMAS)
    missing: list[str] = []
    bad_args: list[str] = []
    for path in files_under("skills", "commands", "docs"):
        text = read(path)
        for tool in sorted(set(re.findall(r"mcp__tars_vault__([A-Za-z_][A-Za-z0-9_]*)", text))):
            if tool not in tools:
                missing.append(f"{path.relative_to(ROOT)}: {tool}")
        for m in re.finditer(r"mcp__tars_vault__([A-Za-z_][A-Za-z0-9_]*)\((.*?)\)", text, re.DOTALL):
            tool = m.group(1)
            if tool not in tools:
                continue
            props = set(TOOL_SCHEMAS[tool]["inputSchema"].get("properties", {}))
            args = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", m.group(2)))
            unknown = sorted(arg for arg in args if arg not in props)
            if unknown:
                bad_args.append(f"{path.relative_to(ROOT)}: {tool} unknown args {unknown}")
    if missing:
        fail("missing tars-vault tools referenced:\n  " + "\n  ".join(missing))
    else:
        pass_("all referenced tars-vault tools exist")
    if bad_args:
        fail("skill examples use unsupported tars-vault args:\n  " + "\n  ".join(bad_args))
    else:
        pass_("tars-vault tool examples match declared argument schemas")


def validate_command_registry() -> None:
    commands = {path.stem for path in (ROOT / "commands").glob("*.md") if path.name != "README.md"}
    missing: list[str] = []
    for skill in (ROOT / "skills").iterdir():
        skill_file = skill / "SKILL.md"
        if not skill_file.is_file():
            continue
        text = read(skill_file)
        if "user-invocable: true" in text and skill.name not in commands:
            missing.append(skill.name)
    if missing:
        fail(f"user-invocable skills without command wrappers: {missing}")
    else:
        pass_("every user-invocable skill has a command wrapper")

    table = read(ROOT / "commands" / "README.md")
    if "Natural-language example" not in table:
        fail("commands/README.md lacks natural-language examples")
    else:
        pass_("command registry includes natural-language examples")

    missing_rows = sorted(cmd for cmd in commands if f"`/{cmd}`" not in table)
    if missing_rows:
        fail(f"commands missing from commands/README.md: {missing_rows}")
    else:
        pass_("commands/README.md lists every command")


def validate_user_facing_docs() -> None:
    docs = [
        ROOT / "README.md",
        ROOT / "docs" / "GETTING-STARTED.md",
        ROOT / "docs" / "CATALOG.md",
        ROOT / "docs" / "MOBILE-USAGE.md",
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
    ]
    forbidden = [
        r"Obsidian-native",
        r"vault required",
        r"Obsidian\s+(is\s+)?required",
        r"requires\s+Obsidian",
        r"obsidian-cli.*required",
        r"install .*tars-vault MCP server",
        r"/tars:",
        r"edit `?INBOX\.md`?",
        r"Add items to `?INBOX\.md`?",
    ]
    hits: list[str] = []
    for path in docs:
        text = read(path)
        for pattern in forbidden:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(f"{path.relative_to(ROOT)}: {pattern}")
    if hits:
        fail("user-facing docs contain stale setup language:\n  " + "\n  ".join(hits))
    else:
        pass_("user-facing docs avoid Obsidian-required, external-MCP, /tars, and INBOX.md guidance")


def validate_welcome_contract() -> None:
    welcome = read(ROOT / "skills" / "welcome" / "SKILL.md")
    for needle in (
        "Markdown files are\n> plain text files",
        "If you don't know what Obsidian is, leave it disabled",
        "local TARS helper is not connected",
        "not an\nObsidian, calendar, task, email, or Slack issue",
        "Paste a meeting transcript, PDF/report excerpt, email thread, or rough notes",
        "memory candidates, journal notes, and\ntasks",
    ):
        if needle not in welcome:
            fail(f"welcome missing required nontechnical setup copy: {needle!r}")
            return
    if "First thing you want TARS to help with" in welcome:
        fail("welcome still asks open-ended first-use-case question")
    else:
        pass_("welcome includes nontechnical helper recovery and prescribed first demo")


def validate_required_tool_surface() -> None:
    required = {
        "scaffold_workspace",
        "read_note",
        "write_note_from_content",
        "create_note",
        "append_note",
        "update_frontmatter",
        "archive_note",
        "fts_search",
        "semantic_search",
        "runtime_info",
        "resolve_alias",
    }
    missing = sorted(required - set(TOOL_SCHEMAS))
    if missing:
        fail(f"required helper tools missing from schema: {missing}")
    else:
        pass_("required helper tools are declared in server schemas")


def main() -> int:
    validate_tool_references()
    validate_command_registry()
    validate_user_facing_docs()
    validate_welcome_contract()
    validate_required_tool_surface()
    if FAIL:
        print("ONE OR MORE CONTRACT CHECKS FAILED")
        return 1
    print("ALL FRAMEWORK CONTRACT CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

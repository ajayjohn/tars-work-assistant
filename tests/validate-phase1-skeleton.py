#!/usr/bin/env python3
"""Validate the Phase 1a/1b skeleton surface added in v3.1 development.

Checks — all structural, no external deps:
  1. mcp/tars-vault package exists with expected tools (no tars-office — PRD §3.1b
     delegates office rendering to Anthropic's first-party skills).
  2. hooks/ has the six lifecycle scripts + hooks.json wiring.
  3. scripts/ has the five new Phase 1a/1b skeletons + capability-classifier.yaml.
  4. requirements.txt exists at the repo root.
  5. .claude-plugin/mcp-servers.json declares tars-vault (only).
  6. templates/integrations-v2.md exists and carries the v2.0 marker.
  7. scripts/githooks/ has prepare-commit-msg, pre-push, install-githooks.sh.
  8. No stray references to a tars-office package remain.

Exits non-zero on any failure.
"""
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_VAULT_TOOLS = {
    "append_note.py",
    "archive_note.py",
    "classify_file.py",
    "create_note.py",
    "detect_near_duplicates.py",
    "fts_search.py",
    "move_note.py",
    "read_note.py",
    "refresh_integrations.py",
    "rerank.py",
    "resolve_capability.py",
    "scan_secrets.py",
    "search_by_tag.py",
    "semantic_search.py",
    "update_frontmatter.py",
    "write_note_from_content.py",
}

EXPECTED_HOOKS = {
    "session-start.py",
    "pre-tool-use.py",
    "post-tool-use.py",
    "pre-compact.py",
    "session-end.py",
    "instructions-loaded.py",
}

EXPECTED_NEW_SCRIPTS = {
    "discover-mcp-tools.py",
    "capability-classifier.py",
    "build-search-index.py",
    "fix-wikilinks.py",
    "migrate-integrations-v2.py",
}

EXPECTED_GITHOOKS = {
    "prepare-commit-msg",
    "pre-push",
    "install-githooks.sh",
}


def check_dir_members(base: Path, expected: set[str]) -> list[str]:
    errors: list[str] = []
    if not base.is_dir():
        return [f"missing directory: {base.relative_to(ROOT)}"]
    present = {entry.name for entry in base.iterdir() if entry.is_file()}
    for name in expected:
        if name not in present:
            errors.append(f"missing {base.relative_to(ROOT)}/{name}")
    return errors


def main() -> int:
    errors: list[str] = []

    # 1. MCP tool packages (tars-vault only — office delegates per §3.1b)
    errors += check_dir_members(
        ROOT / "mcp" / "tars-vault" / "src" / "tars_vault" / "tools",
        EXPECTED_VAULT_TOOLS,
    )
    for must_exist in (
        "mcp/tars-vault/pyproject.toml",
        "mcp/tars-vault/src/tars_vault/__main__.py",
        "mcp/tars-vault/src/tars_vault/server.py",
        "mcp/tars-vault/src/tars_vault/validators.py",
        "mcp/tars-vault/tests/test_skeleton.py",
    ):
        if not (ROOT / must_exist).is_file():
            errors.append(f"missing file: {must_exist}")
    # 1b. tars-office must NOT exist (PRD §3.1b / §26.4 removal)
    office_dir = ROOT / "mcp" / "tars-office"
    if office_dir.exists():
        errors.append(
            "mcp/tars-office/ must not exist — office rendering delegates to "
            "Anthropic's first-party skills per PRD §3.1b"
        )

    # 2. Hooks
    errors += check_dir_members(ROOT / "hooks", EXPECTED_HOOKS)
    if not (ROOT / "hooks" / "hooks.json").is_file():
        errors.append("missing file: hooks/hooks.json")

    # 3. New scripts + classifier YAML
    errors += check_dir_members(ROOT / "scripts", EXPECTED_NEW_SCRIPTS)
    if not (ROOT / "scripts" / "capability-classifier.yaml").is_file():
        errors.append("missing file: scripts/capability-classifier.yaml")

    # 4. requirements.txt
    if not (ROOT / "requirements.txt").is_file():
        errors.append("missing file: requirements.txt")

    # 5. MCP server registration
    mcp_servers = ROOT / ".claude-plugin" / "mcp-servers.json"
    if not mcp_servers.is_file():
        errors.append("missing file: .claude-plugin/mcp-servers.json")
    else:
        try:
            manifest = json.loads(mcp_servers.read_text(encoding="utf-8"))
            servers = manifest.get("mcpServers", {})
            if "tars-vault" not in servers:
                errors.append(".claude-plugin/mcp-servers.json missing server: tars-vault")
            if "tars-office" in servers:
                errors.append(
                    ".claude-plugin/mcp-servers.json must not declare tars-office "
                    "(PRD §3.1b delegates office rendering to Anthropic skills)"
                )
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON in .claude-plugin/mcp-servers.json: {exc}")

    # 6. v3.1 integrations template
    template = ROOT / "templates" / "integrations-v2.md"
    if not template.is_file():
        errors.append("missing file: templates/integrations-v2.md")
    else:
        if 'tars-config-version: "2.0"' not in template.read_text(encoding="utf-8"):
            errors.append("templates/integrations-v2.md: missing tars-config-version: \"2.0\" marker")

    # 7. git hooks
    errors += check_dir_members(ROOT / "scripts" / "githooks", EXPECTED_GITHOOKS)
    for name in ("prepare-commit-msg", "pre-push", "install-githooks.sh"):
        path = ROOT / "scripts" / "githooks" / name
        if path.is_file() and not os.access(path, os.X_OK):
            errors.append(f"scripts/githooks/{name} is not executable")

    # Report
    print("=" * 60)
    print("TARS v3.1 Phase 1a/1b Skeleton Validation")
    print("=" * 60)
    if errors:
        print()
        print(f"ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  ✗ {err}")
        print()
        print("STATUS: FAIL")
        return 1
    print()
    print("  ✓ Phase 1a/1b skeleton surface is complete")
    print()
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

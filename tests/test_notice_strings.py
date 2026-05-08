#!/usr/bin/env python3
"""Lint user-facing SessionStart notice strings.

PRD-03 / UX-1, UX-7, UX-8, UX-10. Catches regressions where contributors
re-introduce raw shell commands, MCP tool names, or other implementation
jargon into strings the user reads on session start.

The lint extracts string literals from `hooks/session-start.py` that look
like notice text — function names ending in `_notice`, plus literals
appended to a `parts.append(...)` or returned from an `_notice`-suffixed
function — and asserts none of them contain forbidden patterns.

Runs as part of the standard test suite; also wired into CI by
`.github/workflows/validate.yml`.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_FILE = ROOT / "hooks" / "session-start.py"

# Patterns that must NOT appear in user-facing notice strings.
# Each entry: (regex, human-readable rule, allow_in_blocking_error_only)
FORBIDDEN_RULES: list[tuple[re.Pattern[str], str, bool]] = [
    # raw shell invocation of a TARS script
    (re.compile(r"python3\s+(?:scripts/|\$\{CLAUDE_PLUGIN_ROOT\})"),
     "raw shell command — use a slash command instead",
     # the unexpanded-env banner is allowed to point at the relocate script
     # because the user's session is already broken at that point and the
     # one-line slash equivalent isn't enough; everywhere else is forbidden.
     True),
    # MCP tool name leaking
    (re.compile(r"mcp__[a-z0-9_]+__[a-z0-9_]+"),
     "MCP tool name — use a slash command, or auto-do the action",
     False),
    # internal yaml filenames
    (re.compile(r"_system/[A-Za-z0-9_-]+\.(?:yaml|yml)"),
     "internal yaml filename — paraphrase ('the install record', 'integrations index')",
     # the unexpanded-env banner names .mcp.json which is a user-edited file;
     # _system/* yaml is always internal, no exception.
     False),
    # phantom step references
    (re.compile(r"step\s*\d+\b", re.IGNORECASE),
     "phantom 'step N' reference — use a labeled slash command flag",
     False),
    # the word "cron" — implementation jargon
    (re.compile(r"\bcron(?:\s|\b)"),
     "the word 'cron' — say 'scheduled jobs' or 'schedules'",
     False),
]

# Functions whose returned strings are user-visible.
USER_FACING_FUNCTIONS = {
    "_no_workspace_hint",
    "_unexpanded_env_notice",
    "_worktree_notice",
    "_vault_notice",
    "_claude_home_workspace_notice",
    "_welcome_back_notice",
    "_version_drift_notice",
    "_pollution_notice",
    "_registry_notice",
    "_cron_notice",
    "_migration_notice",
}

# A function may legitimately return a hardened-error notice that must
# reference the user's MCP config file. Track those by name so a single rule
# can be relaxed for them.
BLOCKING_ERROR_NOTICES = {"_unexpanded_env_notice"}


def _string_literals_in_function(tree: ast.Module, func_name: str) -> list[tuple[str, int]]:
    """Return [(string_value, lineno)] for every str constant in a function body."""
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    out.append((sub.value, sub.lineno))
                # f-strings are JoinedStr whose Constant parts are FormattedValue siblings
                if isinstance(sub, ast.JoinedStr):
                    rendered = "".join(
                        v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else "{…}"
                        for v in sub.values
                    )
                    out.append((rendered, sub.lineno))
    return out


def lint_notice_strings() -> list[str]:
    """Return a list of violations. Empty list = clean."""
    src = HOOKS_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(HOOKS_FILE))
    violations: list[str] = []
    for func in USER_FACING_FUNCTIONS:
        is_blocking = func in BLOCKING_ERROR_NOTICES
        for value, line in _string_literals_in_function(tree, func):
            if not value.strip():
                continue
            for rx, rule, allow_blocking in FORBIDDEN_RULES:
                if rx.search(value):
                    if allow_blocking and is_blocking:
                        continue
                    snippet = value if len(value) <= 120 else value[:117] + "..."
                    violations.append(
                        f"{HOOKS_FILE.name}:{line}: in {func}(): {rule}\n"
                        f"  string: {snippet!r}"
                    )
    return violations


def main() -> int:
    if not HOOKS_FILE.is_file():
        print(f"FAIL: {HOOKS_FILE} not found", file=sys.stderr)
        return 1
    violations = lint_notice_strings()
    if violations:
        print(f"test_notice_strings: {len(violations)} violation(s)\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        return 1
    print(f"test_notice_strings: clean ({len(USER_FACING_FUNCTIONS)} notice functions checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

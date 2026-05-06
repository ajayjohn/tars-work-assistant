# TARS v3.2 hooks

Claude Code lifecycle hooks. Wired in via `.claude/settings.json` (plugin-level)
and enforced by the Claude Code harness at the correct lifecycle events.

Status: active. Hooks read stdin events, enforce workspace-write guardrails,
emit telemetry where appropriate, route session transcripts into the inbox, and
exit 0 for observability-only lifecycle events.

| Hook | Lifecycle | Purpose |
|------|-----------|---------|
| `session-start.py` | SessionStart | staleness banner, reach-ability checks, alias-registry head-load, cron health |
| `pre-tool-use.py` | PreToolUse | block obsidian `create` with no args; warn on >40KB payload; enforce `tars-` prefix |
| `post-tool-use.py` | PostToolUse | emit `vault_write` telemetry event on successful vault-mutating MCP calls |
| `pre-compact.py` | PreCompact | flush decisions/commitments to `inbox/pending/claude-session-*.md` |
| `session-end.py` | SessionEnd | same as PreCompact for sessions that close without compacting |
| `instructions-loaded.py` | InstructionsLoaded | append `skill_loaded` to telemetry jsonl |

All hooks follow the template in PRD §26.5. SessionStart and InstructionsLoaded
must never exit non-zero. PreToolUse may exit 2 (deny) with a message on stderr.

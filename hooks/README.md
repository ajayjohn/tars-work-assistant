# TARS v3.1 hooks

Claude Code lifecycle hooks. Wired in via `.claude/settings.json` (plugin-level)
and enforced by the Claude Code harness at the correct lifecycle events.

Status: **skeleton (Phase 1a)**. Side-effects (telemetry writes, inbox routing,
changelog append) land in later phases per PRD §10. In skeleton form they read
stdin, validate the environment, and exit 0 without writing.

| Hook | Lifecycle | Purpose |
|------|-----------|---------|
| `session-start.py` | SessionStart | staleness banner, reach-ability checks, alias-registry head-load, cron health |
| `pre-tool-use.py` | PreToolUse | block obsidian `create` with no args; warn on >40KB payload; enforce `tars-` prefix |
| `post-tool-use.py` | PostToolUse | append changelog row; dedupe backlog issues on failure |
| `pre-compact.py` | PreCompact | flush decisions/commitments to `inbox/pending/claude-session-*.md` |
| `session-end.py` | SessionEnd | same as PreCompact for sessions that close without compacting |
| `instructions-loaded.py` | InstructionsLoaded | append `skill_loaded` to telemetry jsonl |

All hooks follow the template in PRD §26.5. SessionStart and InstructionsLoaded
must never exit non-zero. PreToolUse may exit 2 (deny) with a message on stderr.

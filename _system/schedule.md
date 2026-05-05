---
tags:
  - tars/system
tars-created: 2026-03-21
tars-modified: 2026-05-05
---

# Schedule

## Recurring Scheduled Tasks

Machine-readable state lives in `_system/housekeeping-state.yaml` (cron_jobs block).
This table is the human-readable display — updated automatically by /welcome Step 7
and /maintain when jobs are registered, re-registered, or cancelled.

| Task | Schedule | Scheduler | Job ID | Registered At | Confirm Before Run | Status |
|------|----------|-----------|--------|---------------|--------------------|--------|
| Daily Briefing | (set during onboarding) | — | — | — | false | pending setup |
| Weekly Briefing | (set during onboarding) | — | — | — | false | pending setup |
| Weekly Maintenance | Sun 18:00 CT | — | — | — | false | pending setup |
| Nightly Lint | (set during onboarding) | — | — | — | false | pending setup |

**Scheduler column values:**
- `mcp__scheduled-tasks` — persistent MCP server scheduler (no expiry; Claude Code only)
- `CronCreate` — built-in Claude tool scheduler (~7-day TTL; visible in Cowork + Claude Code)
- `—` — not yet registered

**Mutual exclusion**: Each job may only be registered with ONE scheduler at a time.
A machine running both Claude Desktop (Cowork) and Claude Code has access to both
schedulers simultaneously — registering the same job with both would cause duplicate
execution. The `housekeeping-state.yaml` `scheduler_type` field is the authoritative
lock: always check it before registration and never override it without explicit
user approval.

## Scheduler Preference

1. **`mcp__scheduled-tasks`** (preferred when available): persistent, no TTL, no weekly
   re-registration needed. Visible only in Claude Code scheduler panel.
2. **`CronCreate`** (fallback): expires after ~7 days. Visible in both Cowork and
   Claude Code scheduler panels. Automatically re-registered by `/maintain` weekly
   and by SessionStart when expiry is within 2 days.

## One-Time Scheduled Items

(Added by workflows as needed)

## Confirm-Before-Run

When `confirm_before_run: true` is set for a job (configurable per-job in
`housekeeping-state.yaml`), the cron-fired session presents a prompt instead of
running immediately:

> TARS jobs due: [1] Daily briefing [2] Weekly briefing — accept / skip / postpone?

User options:
- **Accept** — run the job now
- **Skip** — do not run; log a skip entry to journal
- **Postpone N hours** — re-arm the job at now + N (default 2h)

If no user response within `auto_timeout_hours` (default 4h), the
`auto_timeout_action` setting determines behavior: `run` (auto-execute) or
`skip` (cancel for today). Fully-automatic execution is preserved by setting
`confirm_before_run: false` (the default).

## Schedule Notes

- `housekeeping-state.yaml` is the authoritative machine-readable state for all job IDs,
  scheduler types, and confirm-before-run settings.
- This file (`schedule.md`) is the human-readable display, updated on each registration.
- SessionStart re-registers CronCreate jobs when expiry is within 2 days (TTL = 7 days).
- SessionStart NEVER switches a job from one scheduler to another — that requires explicit
  user action via `/welcome --re-register` or `/maintain`.
- If a job was registered with `mcp__scheduled-tasks` and is still active there, the
  SessionStart and /maintain flows skip re-registration entirely for that job.

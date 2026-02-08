# TARS shortcuts

Shortcut definitions for Cowork scheduled execution. These are created during the welcome flow or manually by the user via the `create-shortcut` skill.

## daily-housekeeping

**Schedule:** `30 17 * * *` (5:30 PM daily, configurable during setup)

**Task description:**

```
Run the TARS daily housekeeping pipeline. This is a silent maintenance pass that keeps the workspace healthy.

Steps:
1. Read reference/.housekeeping-state.yaml to check if housekeeping has already run today. If last_run equals today's date, exit early with no action.
2. Run the archival sweep: execute `python3 scripts/archive.py {workspace_path} --auto` to expire ephemeral lines and archive stale content.
3. Run the health check: execute `python3 scripts/health-check.py {workspace_path}` to validate indexes, detect broken wikilinks, and flag naming issues.
4. Run the task sync: execute `python3 scripts/sync.py {workspace_path}` to check scheduled items and detect memory gaps.
5. Count files in inbox/pending/ to track unprocessed inbox items.
6. Update reference/.housekeeping-state.yaml with today's date, success status, incremented run count, and current inbox count.
7. If critical issues are found (broken indexes, overdue scheduled items), save a brief summary to journal/YYYY-MM/YYYY-MM-DD-housekeeping.md for later review.

Success criteria: All three scripts complete without errors. State file updated. No user interaction required.

Constraints:
- Do not prompt the user for input. This runs autonomously.
- Do not process inbox items (that requires user confirmation via /maintain inbox).
- Do not run full index rebuild (expensive, only on demand via /maintain rebuild).
- If any script fails, log the failure and continue with the remaining scripts.
- All scripts use Python standard library only. No pip installs needed.

File paths:
- State file: reference/.housekeeping-state.yaml
- Scripts: scripts/health-check.py, scripts/archive.py, scripts/sync.py
- Inbox: inbox/pending/
- Journal output (if issues found): journal/YYYY-MM/YYYY-MM-DD-housekeeping.md
```

### Creating this shortcut

During the welcome flow or at any time, use the `create-shortcut` skill:

1. Invoke `/create-shortcut`
2. Use task name: `daily-housekeeping`
3. Use the task description above
4. Set cron schedule: `30 17 * * *` (or user's preferred time)

The session-start check in the core skill serves as a fallback if this shortcut is not configured or the environment does not support scheduled shortcuts.

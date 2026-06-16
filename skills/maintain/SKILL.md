---
name: maintain
description: Maintain workspace intake, sync, archive, context gaps, weekly review, and harness health
user-invocable: true
triggers:
  - "run maintenance"
  - "housekeeping"
  - "process inbox"
  - "check inbox"
  - "sync"
  - "check for gaps"
  - "archive sweep"
  - "clean up workspace"
  - "list worktrees"
help:
  purpose: |-
    Keep TARS useful over time by processing intake, detecting context gaps,
    syncing external boundaries, proposing archive candidates, and surfacing
    harness review items.
  use_cases:
    - "Process my inbox"
    - "Check for gaps"
    - "Clean up stale context"
    - "Run maintenance"
  scope: maintenance,inbox,sync,archive,gaps,harness,worktrees
---

# Maintain

Maintenance is the time-and-drift control plane. Prefer natural-language
workflow names in user output. Slash commands remain shortcuts.

## Modes

| Intent | Mode |
|---|---|
| Process pending files or session captures | inbox |
| Find missing context from calendar/tasks/inbox/activity | gaps |
| Compare workspace to external systems | sync |
| Propose lifecycle archival | archive |
| Produce weekly review queue | weekly |
| Inspect git worktree clutter | worktrees |

## Non-negotiables

- Never delete files.
- Never auto-apply archive, memory, task, or harness changes.
- Run core extension pre-flight before every mode. Enabled extensions whose
  triggers match "process inbox", "run maintenance", "sync", or the active mode
  must be loaded before scanning files or checking external drift.
- Archive is active-set management, not punishment for old files.
- Weekly maintenance includes a Harness review section.
- Heavy scans belong in maintenance, not SessionStart.

## References

- `references/inbox.md`
- `references/sync.md`
- `references/archive.md`
- `references/weekly.md`
- `references/legacy-full-protocol.md`

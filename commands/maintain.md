---
description: Inbox processing, calendar/task sync, archive sweep, and scheduled housekeeping for the TARS workspace
argument-hint: "[inbox | sync | archive | --comprehensive]"
---

# /maintain

## Protocol
Before following the skill, run the TARS extension pre-flight for `skill="maintain"` using the selected maintenance mode and user intent: `list_extensions` → `resolve_extension` → `read_extension` for matches → resolve declared capabilities.

Read and follow `skills/maintain/`

Modes: inbox, sync, archive, or the default "run maintenance" which combines archive + sync. Inbox mode can bulk-process files in `inbox/pending/`, including transcripts, PDFs, decks, docs, screenshots, exports, and rough notes. Hygiene checks (broken links, orphans, schema violations, staleness, contradictions, framework state drift) moved to `/lint` in v3.1. Automatic daily housekeeping runs via SessionStart hook when `_system/housekeeping-state.yaml.last_run` is not today.

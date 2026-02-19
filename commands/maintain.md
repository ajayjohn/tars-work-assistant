---
description: Workspace health checks, task sync, memory gap detection, index rebuilding, inbox processing, and reference file updates
argument-hint: "[health | sync | rebuild | inbox | update | --comprehensive]"
---

# /maintain

## Protocol
Read and follow `skills/maintain/`

Modes: health (default), sync, rebuild, inbox, update. Add --comprehensive for deep scan in sync mode. Automatic daily housekeeping (health check, archive sweep, task sync) runs at session start without user intervention. Update mode checks workspace reference files against the installed plugin version and applies updates while preserving user customizations.

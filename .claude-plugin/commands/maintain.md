---
description: Workspace health checks, task sync, memory gap detection, index rebuilding, and inbox processing
argument-hint: "[health | sync | rebuild | inbox | --comprehensive]"
---

# /maintain

## Protocol
Read and follow `skills/maintain/`

Modes: health (default), sync, rebuild, inbox. Add --comprehensive for deep scan in sync mode. Automatic daily housekeeping (health check, archive sweep, task sync) runs at session start without user intervention.

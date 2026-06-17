---
description: Extract tasks from input or manage existing tasks
argument-hint: "[extract | manage | review]"
---

# /tasks

## Protocol
Before following the skill, run the TARS extension pre-flight for `skill="tasks"` using the selected task mode and user intent: `list_extensions` → `resolve_extension` → `read_extension` for matches → resolve declared capabilities.

Read and follow `skills/tasks/`

Default: detect mode from context. "extract" for task extraction, "manage" or "review" for task management.

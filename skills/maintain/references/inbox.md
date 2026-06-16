# Inbox Maintenance Reference

## Mandatory pre-flight

Before scanning `inbox/pending/`, run the core extension pre-flight:

1. `mcp__tars_vault__list_extensions`.
2. `mcp__tars_vault__resolve_extension(skill="maintain", mode="inbox")`.
3. `mcp__tars_vault__read_extension` for every resolved enabled extension.
4. If an extension's "When To Load" triggers match "process inbox", "run
   maintenance", or the user's current intent, follow that extension under
   maintain's review gates.
5. For every capability declared by a matched extension, call
   `mcp__tars_vault__resolve_capability(capability="<capability>")` before
   deciding no external-provider work is needed.

Inventory `inbox/pending/`, classify each item, and ask before processing bulk
work. Supported routes include meeting, learn, tasks, companion context, and
archive.

Never mark unreadable binary files as processed. Create or request a companion
text representation instead.

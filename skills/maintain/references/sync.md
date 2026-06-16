# Sync Maintenance Reference

## Mandatory pre-flight

Before checking calendar gaps, task drift, or workspace/external drift, run the
core extension pre-flight:

1. `mcp__tars_vault__list_extensions`.
2. `mcp__tars_vault__resolve_extension(skill="maintain", mode="sync")`.
3. `mcp__tars_vault__read_extension` for every resolved enabled extension.
4. If an extension's "When To Load" triggers match "sync", "run maintenance",
   or the user's current intent, follow that extension under maintain's review
   gates.
5. For every capability declared by a matched extension, call
   `mcp__tars_vault__resolve_capability(capability="<capability>")` before
   deciding no external-provider work is needed.

Sync compares workspace state to external capabilities:

- calendar gaps
- task drift
- stale people after recent meetings
- stale active initiatives

Resolve integrations by capability with explicit
`mcp__tars_vault__resolve_capability` calls. Surface drift for review; never
auto-fix external state.

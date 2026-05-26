# Harness Reference

TARS treats its AI layer as product code: instructions, skills, hooks, MCP
tools, schemas, telemetry, tests, and packaging.

## Budget rules

- `CLAUDE.md` and `skills/core/SKILL.md` are the always-loaded core.
- User-invocable `SKILL.md` files are router cards.
- Long procedures live in `references/` and load only by workflow mode.
- Subagents may explore but must return bounded JSON or concise summaries.

## Harness review

Weekly maintenance surfaces review-only proposals for:

- repeated skill failures
- routing misses
- stale or unused workflow aliases
- bloated skill cards
- instructions contradicted by implementation
- memories or tasks created but never retrieved
- stale dynamic state capsules

Never auto-edit `CLAUDE.md`, skills, schemas, templates, or command wrappers.


---
description: Vault hygiene — broken links, orphans, schema violations, staleness, contradictions, framework state drift
argument-hint: "[--focus links | orphans | schema | stale | contradictions | framework | organize]"
---

# /lint

## Protocol
Before following the skill, run the TARS extension pre-flight for `skill="lint"` using the requested focus as intent: `list_extensions` → `resolve_extension` → `read_extension` for matches → resolve declared capabilities.

Read and follow `skills/lint/`

The third TARS operation alongside `ingest` and `query`. Surfaces consistency and hygiene issues, proposes fixes, and applies deterministic ones after user review. Runs automatically nightly via CronCreate (see §26.7).

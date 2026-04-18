---
description: Vault hygiene — broken links, orphans, schema violations, staleness, contradictions, framework state drift
argument-hint: "[--focus links | orphans | schema | stale | contradictions | framework | organize]"
---

# /lint

## Protocol
Read and follow `skills/lint/`

The third TARS operation alongside `ingest` and `query`. Surfaces consistency and hygiene issues, proposes fixes, and applies deterministic ones after user review. Runs automatically nightly via CronCreate (see §26.7).

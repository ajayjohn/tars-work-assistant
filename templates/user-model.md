---
tags: [tars/user-model]
tars-summary: "Observed user preferences inferred from telemetry — distinct from declared config."
tars-created: ""
tars-modified: ""
tars-last-pattern-scan: ""
# Observed preferences (inferred). Declared equivalents live in _system/config.md;
# /lint flags drift between observed and declared.
tars-bluf-tolerance: ""           # high | medium | low | unset
tars-decision-speed: ""           # fast | deliberate | slow | unset
tars-default-skill: ""            # most-invoked skill in the last 14 days
tars-meeting-cadence: ""          # daily | several-per-day | a-few-per-week | rare | unset
tars-recurring-concerns: []       # list of free-text concerns surfaced 3+ times in 14d
tars-vendor-sentiment: {}         # map: vendor name → "positive" | "neutral" | "skeptical"
tars-observed-skill-mix: {}       # map: skill name → count over last 14d
---

# Observed preferences (user model)

This note captures patterns TARS has inferred passively from telemetry — what you *do*, not what you *said* during onboarding. The contents are read by `core` for routing decisions and by `communicate` / `briefing` to bias output style. The declared equivalents live in `_system/config.md`; `/lint` surfaces drift between the two.

## How this gets updated

`/learn` runs a pattern-detection pass during `/maintain --weekly` (cron-fired) and inside an explicit `/learn --review-patterns` invocation. A pattern needs to repeat **at least 3 times in 14 days** of telemetry before it proposes an update. Every change is reviewed before persist — nothing is auto-applied.

The pass is read-mostly:

- Counts of `skill_loaded` / `vault_write` per skill drive `tars-observed-skill-mix` and `tars-default-skill`.
- `briefing_generated` cadence and `meeting_processed` event volume drive `tars-meeting-cadence`.
- Sentiment markers in transcript and `/communicate` outputs that mention specific vendors update `tars-vendor-sentiment` (3+ negative mentions → "skeptical"; 3+ positive → "positive"; otherwise neutral).
- Recurring topics that appear in `/think`, `/learn` save events, and `/answer` queries roll up into `tars-recurring-concerns`.
- `tars-bluf-tolerance` flips to `low` when the user repeatedly asks for "more detail" or "expand" after BLUF outputs; flips to `high` when the user repeatedly says "shorter" / "tl;dr".

## Constraints

- This file is TARS-managed. The user may edit any value to override an inference, but the next pattern scan will respect explicit overrides only if `tars-pinned: true` appears at the field level (set per-field in a sidecar `tars-pinned-fields:` list, planned for Phase 7).
- Maximum file size ~5 KB. Lists and maps are bounded — top 20 entries by recency for `tars-observed-skill-mix`, top 10 for `tars-recurring-concerns`, top 50 for `tars-vendor-sentiment`. Older entries are evicted.
- Empty strings and `{}` / `[]` are valid initial values; the file ships empty after `/welcome` and accumulates over weeks.

---
tars-persona-key: product-leader
tars-persona-name: Product Leader
tars-persona-summary: Owns roadmap, customer signals, and feature decisions across one or more product lines.
tars-config-defaults:
  tars-bluf-level: high
  tars-default-analysis-mode: B
  tars-review-gate-strictness: standard
  tars-briefing-style: executive
tars-taxonomy-tags:
  - tars/customer-segment
  - tars/feature
  - tars/hypothesis
  - tars/market-signal
  - tars/roadmap-item
  - tars/release
  - tars/competitor-move
tars-briefing-sections:
  - top-priorities
  - customer-signals
  - roadmap-risks
  - active-initiatives
  - decisions-pending
  - upcoming-meetings
---

# Product Leader

You own outcomes for a product or product line: roadmap, prioritization, customer discovery, release decisions, and stakeholder alignment across engineering, design, sales, and exec.

TARS will bias toward:
- **BLUF executive style** — top line first, supporting detail one level deep, no preamble.
- **Customer-signal capture** — every meeting transcript is scanned for explicit customer asks, anti-asks, and willingness-to-pay signals; surfaced in the daily briefing.
- **Roadmap awareness** — initiatives tagged with `tars/roadmap-item` are joined against decisions and customer signals when generating /briefing and /think outputs.
- **Decision pressure** — pending decisions older than 7 days surface in the briefing footer.

Default analysis mode is `B` (Strategic Council) for stress-testing positioning and prioritization tradeoffs. Switch to mode `A` for adversarial pre-mortems before launches.

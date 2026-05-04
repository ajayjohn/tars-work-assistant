---
tars-persona-key: delivery-pm
tars-persona-name: Delivery / Project Manager
tars-persona-summary: Owns schedule, scope, dependencies, and RAID across one or more programs.
tars-default-mode: standard
tars-config-defaults:
  tars-bluf-level: medium
  tars-default-analysis-mode: C
  tars-review-gate-strictness: standard
  tars-briefing-style: operational
tars-taxonomy-tags:
  - tars/milestone
  - tars/blocker
  - tars/dependency
  - tars/sprint
  - tars/raid-risk
  - tars/raid-assumption
  - tars/raid-issue
  - tars/raid-decision
  - tars/critical-path
tars-briefing-sections:
  - active-blockers
  - schedule-risks
  - dependencies-due
  - todays-standups
  - milestones-this-week
  - decisions-pending
---

# Delivery / Project Manager

You keep programs on schedule. Days are spent unblocking dependencies, running standups and steering committees, updating RAID logs, and reporting status up.

TARS will bias toward:
- **Operational briefing style** — active blockers first (with owner + age), then schedule risks, then dependencies due this week.
- **RAID hygiene** — risks/assumptions/issues/decisions captured from meetings get tagged automatically; stale risks (no update in 14 days) surface as briefing risks.
- **Milestone awareness** — initiatives with `tars-target-date` within 14 days are foregrounded; `tars-health: red` initiatives appear in every briefing until they recover.
- **Standard review gates** — schedule and milestone changes always confirm; standup notes auto-file.

Default analysis mode is `C` (Critical Path) for surfacing the longest dependency chain and where slack has been consumed.

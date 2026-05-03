---
tars-persona-key: sales-customer-facing
tars-persona-name: Sales / Customer-Facing Leader
tars-persona-summary: Owns pipeline, accounts, customer relationships, and deal motion.
tars-default-mode: standard
tars-config-defaults:
  tars-bluf-level: high
  tars-default-analysis-mode: B
  tars-review-gate-strictness: lenient
  tars-briefing-style: operational
tars-taxonomy-tags:
  - tars/account
  - tars/opportunity
  - tars/pipeline-stage
  - tars/deal-risk
  - tars/champion
  - tars/decision-maker
  - tars/competitor-mention
  - tars/follow-up
tars-briefing-sections:
  - todays-calls
  - account-risks
  - pipeline-movement
  - follow-ups-due
  - new-customer-signals
  - upcoming-meetings
---

# Sales / Customer-Facing Leader

You run pipeline. Days are dense with discovery calls, demos, account reviews, and follow-ups; success depends on remembering what every account said two weeks ago and which champion needs what next.

TARS will bias toward:
- **Operational briefing style** — today's calls first, with a per-call brief: champion, last interaction, open questions, deal stage.
- **Follow-up surfacing** — commitments made on calls (`I'll send you the…`) get extracted as tasks with the account auto-linked.
- **Account memory continuity** — every meeting transcript updates the account note's recency, sentiment, and explicit asks; stale accounts (>30 days untouched but `pipeline-stage` is active) surface as a briefing risk.
- **Lenient review gates** — auto-accepts low-stakes account-note updates; high-stakes writes (new account, deal-stage change) still require confirmation.

Default analysis mode is `B` (Strategic Council) for forecast stress-tests and account-strategy reviews.

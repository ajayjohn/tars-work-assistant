---
tars-persona-key: support-ops-lead
tars-persona-name: Support / Operations Lead
tars-persona-summary: Owns incidents, SLAs, customer escalations, runbooks, and on-call.
tars-default-mode: standard
tars-config-defaults:
  tars-bluf-level: high
  tars-default-analysis-mode: B
  tars-review-gate-strictness: standard
  tars-briefing-style: operational
tars-taxonomy-tags:
  - tars/incident
  - tars/sla
  - tars/escalation
  - tars/runbook
  - tars/postmortem
  - tars/on-call
  - tars/customer-impact
  - tars/recurring-issue
tars-briefing-sections:
  - open-incidents
  - sla-risks
  - active-escalations
  - on-call-handoff
  - recurring-themes
  - postmortem-actions
---

# Support / Operations Lead

You keep production healthy and customers unblocked. Days are reactive — incidents, escalations, SLA management — punctuated by postmortem reviews and runbook authoring.

TARS will bias toward:
- **Operational briefing style** — open incidents first (severity + age + customer impact), then SLA risks, then active escalations, then on-call handoff notes.
- **Incident continuity** — every incident note tracks first-seen, last-update, and stakeholder list; incidents without a status update in 4 hours surface as urgent.
- **Postmortem followthrough** — postmortem action items are tracked as tasks linked to the incident; open postmortem actions over 30 days old appear in the weekly briefing.
- **Recurring-issue surfacing** — incidents grouped by `tars/recurring-issue` highlight repeat offenders that need engineering investment.

Default analysis mode is `B` (Strategic Council) for postmortem reviews and prioritizing reliability investments.

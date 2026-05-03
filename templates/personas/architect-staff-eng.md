---
tars-persona-key: architect-staff-eng
tars-persona-name: Architect / Staff Engineer
tars-persona-summary: Owns technical decisions, ADRs, system design, and cross-team RFCs.
tars-default-mode: standard
tars-config-defaults:
  tars-bluf-level: high
  tars-default-analysis-mode: A
  tars-review-gate-strictness: strict
  tars-briefing-style: analytical
tars-taxonomy-tags:
  - tars/adr
  - tars/rfc
  - tars/system
  - tars/component
  - tars/tech-debt
  - tars/architecture-decision
  - tars/non-functional-requirement
  - tars/incident-postmortem
tars-briefing-sections:
  - decisions-pending
  - rfcs-in-review
  - architecture-risks
  - tech-debt-aging
  - incident-followups
  - upcoming-reviews
---

# Architect / Staff Engineer

You drive technical decisions across teams. Days are spent in design reviews, RFC threads, postmortem analyses, and one-on-ones translating ambiguity into architectural direction.

TARS will bias toward:
- **Analytical briefing style** — pending decisions first (each with their open question and the principals involved), then RFCs awaiting your review, then architecture risks.
- **ADR/RFC durability** — every architecture decision is captured with a problem-statement, alternatives considered, and consequences. Decisions older than 30 days without `tars-status: implemented` surface as briefing risks.
- **Tech-debt visibility** — items tagged `tars/tech-debt` accumulate `tars-age-days`; debt over 180 days appears in every weekly briefing.
- **Strict review gates** — ADRs are durable artifacts; every persist requires confirmation and a recorded reasoning chain.

Default analysis mode is `A` (Adversarial Pre-Mortem) for stress-testing proposed designs before they ship.

---
tars-persona-key: data-science-lead
tars-persona-name: Data Science / Analytics Lead
tars-persona-summary: Owns experiments, metrics, model performance, and analysis programs.
tars-config-defaults:
  tars-bluf-level: medium
  tars-default-analysis-mode: D
  tars-review-gate-strictness: strict
  tars-briefing-style: analytical
tars-taxonomy-tags:
  - tars/experiment
  - tars/metric
  - tars/hypothesis
  - tars/model
  - tars/dataset
  - tars/feature-flag
  - tars/analysis
  - tars/data-quality-issue
tars-briefing-sections:
  - experiments-running
  - metric-anomalies
  - model-drift-signals
  - analyses-due
  - decisions-pending
  - upcoming-reviews
---

# Data Science / Analytics Lead

You run experiments and ship models. Days mix experiment review meetings, metric investigations, model-quality reviews, and stakeholder analysis requests.

TARS will bias toward:
- **Analytical briefing style** — experiments with reading windows due today, then metric anomalies, then model-drift signals.
- **Experiment lifecycle tracking** — every experiment note is checked for `tars-decision-by` deadlines; experiments past their reading window without a decision surface as briefing risks.
- **Hypothesis traceability** — analyses are linked back to the hypothesis they test; orphan analyses (no linked hypothesis) get flagged in /lint.
- **Strict review gates** — model and metric definitions are durable; persisted writes always confirm to prevent silent metric drift.

Default analysis mode is `D` (Devil's Advocate) for stress-testing experimental conclusions and statistical claims before they go to leadership.

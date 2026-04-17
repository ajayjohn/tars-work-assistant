---
tars-config-version: "2.0"
tags:
  - tars/system
tars-created: 2026-04-17
---

# Integration preferences (v3.1)

For each capability, list preferred MCP-server short-names in priority order.
The capability is fulfilled by the first server that provides a matching tool.
Unknown capabilities are auto-discovered on SessionStart and persisted to
`_system/tools-registry.yaml` (auto-generated, do not hand-edit).

```yaml
capabilities:
  calendar:            { preferred: [apple-calendar, microsoft-365], required: true }
  tasks:               { preferred: [apple-reminders, microsoft-365], required: true }
  email:               { preferred: [microsoft-365] }
  meeting-recording:   { preferred: [minutes-app] }
  office-docs:         { preferred: [microsoft-365] }   # rendered files via Anthropic's pptx/docx/xlsx/pdf skills; live M365 edits via this capability
  file-storage:        { preferred: [microsoft-365] }
  design:              { preferred: [figma] }
  data-warehouse:      { preferred: [snowflake, bigquery, databricks] }
  analytics:           { preferred: [pendo, amplitude, mixpanel] }
  project-tracker:     { preferred: [jira, linear, github] }
  documentation:       { preferred: [confluence, notion, google-docs] }
  monitoring:          { preferred: [datadog, pagerduty] }
  communication:       { preferred: [slack, microsoft-365] }

unavailable_behavior:
  required: block_workflow_with_clear_message
  optional: degrade_gracefully_and_note_gap
```

Add or remove servers freely — TARS matches against whatever SessionStart
discovers and falls back gracefully when a preferred server is unreachable.

Skills never hardcode server names; they call
`mcp__tars_vault__resolve_capability(capability=…)` and use the first matching
tool that the registry returns.

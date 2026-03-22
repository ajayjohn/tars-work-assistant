---
tags:
  - tars/system
tars-created: 2026-03-21
---

# Integration Registry

TARS uses provider-agnostic integration categories. Each category maps to a concrete provider via MCP or native tools.

## Calendar

| Setting | Value |
|---------|-------|
| Category | calendar |
| Provider | (configured during onboarding) |
| Capabilities | list_events, get_event, create_event |
| Notes | Used for meeting context, briefings, schedule queries |

## Task Manager

| Setting | Value |
|---------|-------|
| Category | tasks |
| Provider | (configured during onboarding) |
| Capabilities | list, create, update, complete |
| Notes | Bidirectional sync with vault task notes |

## Project Tracker

| Setting | Value |
|---------|-------|
| Category | project-tracker |
| Provider | (configured during onboarding) |
| Capabilities | list_projects, get_status, list_issues |
| Notes | Initiative status enrichment |

## Communication

| Setting | Value |
|---------|-------|
| Category | communication |
| Provider | (configured during onboarding) |
| Capabilities | send_message, draft |
| Notes | Stakeholder communication delivery |

## Discovery Protocol

When a workflow needs an integration:
1. Check this registry for the configured provider
2. Verify the MCP server is available
3. If unavailable, degrade gracefully and note the gap
4. Never hard-code vendor-specific logic in workflow skills

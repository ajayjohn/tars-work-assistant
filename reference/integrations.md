# Integration registry

This file is retained as a compatibility reference for the repository. In an active TARS 3.0 vault, the runtime source of truth is `_system/integrations.md`.

## Principles

- skills refer to integration categories, not vendor-specific implementations
- calendar and tasks are the most important integrations for day-to-day value
- MCP is the preferred integration path when available
- integration failures should degrade gracefully rather than corrupting vault state

## Core categories

### Calendar

Purpose:
- daily and weekly briefings
- meeting matching
- attendee context
- schedule queries

Required for full value:
- yes

Expected capabilities:
- list events by date range
- inspect event metadata
- optionally create user-authorized events

### Tasks

Purpose:
- task extraction and review
- due-date awareness in briefings
- completion and reprioritization workflows

Required for full value:
- yes

Expected capabilities:
- list tasks
- create tasks
- update or complete tasks

Important rule:
- task creation should be verified after write attempts when the provider supports readback

### Project tracker

Purpose:
- initiative status
- story and blocker lookup
- roadmap support

Required for full value:
- optional

### Documentation

Purpose:
- query external or organizational docs from TARS workflows

Required for full value:
- optional

## Runtime expectations

The runtime integration file should answer:
- what categories are configured
- whether each category is connected
- what operations are safe
- what constraints apply
- where credentials or server details live

The agent should prefer checking live runtime configuration before assuming an integration is unavailable.

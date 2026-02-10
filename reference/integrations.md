# Integration registry

Provider-agnostic integration configuration. Skills reference integration **categories** (calendar, tasks), not specific tools. The registry tells each skill how to execute operations for the configured provider.

**v2.1+ Recommended**: MCP (Model Context Protocol) servers for all integrations.

**Integration tiers**:
- **Mandatory**: Calendar, Tasks/Reminders (core TARS functionality)
- **Optional**: Project tracker, Documentation (enhanced functionality)

Run `/welcome` to configure integrations. Run `scripts/verify-integrations.py` to check health.

---

## Calendar

category: calendar
required: true

### Provider: MCP (Recommended for v2.1+)

**Configuration**: Add calendar MCP server to `.mcp.json`


**Operations**: TARS uses MCP server's native tools:
- `list_events` → Fetch events for date range
- `create_event` → Create new calendar event
- `get_event` → Get event details

**Skills usage**: Check `<mcp_servers>` context for calendar MCP server first. If found, use MCP tools directly.

**Constraints**:
- Date format MUST be YYYY-MM-DD
- Always resolve relative dates before querying
- Only create events with no attendees
- Never update/delete events not created by TARS
- "Focus time" blocks count as available

---

## Tasks

category: tasks
required: true

### Provider: MCP (Recommended for v2.1+)

**Configuration**: Add reminders MCP server to `.mcp.json`

**Operations**: TARS uses MCP server's native tools:
- `list_reminders` → Fetch tasks from list
- `create_reminder` → Create new task
- `complete_reminder` → Mark task complete

**Skills usage**: Check `<mcp_servers>` context for reminders MCP server first. If found, use MCP tools.

**Constraints**:
- Parse notes defensively: missing fields = unknown, not error
- Only create/edit/delete in allowed lists

#### List mapping

| Condition | List |
|-----------|------|
| Has due date, owner is user | Active |
| Has due date, owner is other | Delegated |
| No due date | Backlog |

#### Notes field convention

Metadata is stored as structured text in the notes field:

```
source: journal/YYYY-MM/YYYY-MM-DD-slug.md
created: YYYY-MM-DD
initiative: [[Initiative Name]]
owner: Name
```

---

## Project Tracker

category: project_tracker
required: false
status: not_configured
available_providers: [jira-mcp, linear-mcp, github-issues, azure-devops]
note: "Check <mcp_servers> for configured project tracker. If found, use its tools directly."

### Query intents

| Need | Query intent |
|------|-------------|
| Initiative stories | Items labeled with initiative name |
| Sprint velocity | Items in open/recent sprints |
| Blocked items | Items in blocked status |
| Bug count | Open bugs by severity |

---

## Documentation

category: documentation
required: false
status: not_configured
available_providers: [confluence-mcp, notion-mcp, google-docs-mcp]
note: "Check <mcp_servers> for configured documentation tool. If found, use its tools directly."

### Query intents

| Need | Query intent |
|------|-------------|
| Find page by title | Search for exact or partial title match |
| Search content | Full-text search across documentation |
| Recent changes | Pages modified in last 7 days |

---

## Data Warehouse (placeholder)

category: data_warehouse
required: false
status: not_configured
available_providers: [snowflake-mcp, bigquery-mcp, databricks-mcp]
note: "Future integration for direct data queries, schema exploration, data quality checks."

---

## Analytics (placeholder)

category: analytics
required: false
status: not_configured
available_providers: [amplitude-mcp, mixpanel-mcp, posthog-mcp]
note: "Future integration for dashboard data, KPI metrics, report generation."

---

## Time Tracking (placeholder)

category: time_tracking
required: false
status: not_configured
available_providers: [harvest-mcp, toggl-mcp, clockify-mcp]
note: "Future integration for time/utilization data, billable hours, team capacity."

---

## Monitoring (placeholder)

category: monitoring
required: false
status: not_configured
available_providers: [datadog-mcp, pagerduty-mcp, cloudwatch-mcp]
note: "Future integration for infrastructure health, pipeline reliability, alert/incident data."

---

## How skills use integrations

Skills reference integration categories, not specific tools. **v2.1+ Priority**: Check for MCP servers first, then fall back to legacy providers.

### Priority flow (v2.1+)

1. **Check MCP first**: Look in `<mcp_servers>` context for relevant MCP server (calendar, reminders, etc.)
2. **Use MCP if found**: Use MCP server's native tools directly
3. **Fall back to legacy**: If MCP not found, read `reference/integrations.md` for legacy provider config
4. **Execute or skip**: If legacy configured, execute. If neither exists, note: "[Category] not configured. Run /welcome to set up."
5. **Handle errors**: If configured integration fails, fall back to workspace-only data and report the gap

### MCP discovery at runtime

For any category:
1. Check `<mcp_servers>` context for matching MCP server (preferred)
2. If found, use the MCP server's native operations
3. If not found, check `reference/integrations.md` for legacy provider
4. Map MCP results to the category's expected output format

---

## Error handling

**When an integration is unavailable:**
1. Skip the integration query
2. Proceed with workspace-only data (memory, journal, contexts)
3. Note the gap in the output

**When a configured integration fails:**
1. Acknowledge the error in your response
2. Fall back to workspace file data
3. Never silently skip, always report the gap

**When status is `not_configured`:**
- Skills should gracefully handle the absence
- Continue with reduced functionality
- Clearly state what functionality is unavailable

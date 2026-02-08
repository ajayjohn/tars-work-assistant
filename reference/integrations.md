# Integration registry

Provider-agnostic integration configuration. Skills reference integration **categories** (calendar, tasks), not specific tools. The registry tells each skill how to execute operations for the configured provider.

Run `scripts/verify-integrations.py` to check integration health. Run `/welcome` to configure integrations.

---

## Calendar

category: calendar
required: true
status: configured
provider: eventlink
type: http-api
operations:
  list_events: "GET {base_url}/events.json?date={date}&offset={offset}&selectCalendar={calendar}"
  create_event: "POST {base_url}/events/create?calendar={calendar}"
config:
  base_url: http://localhost:PORT
  calendar: Calendar
  auth: "Bearer TOKEN"
constraints:
  - Date format MUST be YYYY-MM-DD
  - Always resolve relative dates before querying
  - Use date + offset params for fetching, never startDate/endDate
  - Only create events with no attendees
  - Never update/delete events not created by TARS
  - "Focus time" blocks count as available
  - If unreachable, fall back to tasks-only mode and note the gap

### Provider: eventlink (Apple Calendar via HTTP API)

Eventlink is a local HTTP API for Apple Calendar.

#### Fetching events

```
GET {base_url}/events.json?date=YYYY-MM-DD&offset=N&selectCalendar={calendar}
Authorization: Bearer {auth}
```

- `date`: Start date in YYYY-MM-DD format
- `offset`: Number of days to include (1 = single day, 7 = one week)
- `selectCalendar`: Calendar name to filter

Do NOT use `startDate` or `endDate` when fetching events. Those are body fields for the create endpoint only.

#### Creating events

```
POST {base_url}/events/create?calendar={calendar}
Authorization: Bearer {auth}
Content-Type: application/json

{"title": "Event title", "startDate": "YYYY-MM-DD HH:MM", "endDate": "YYYY-MM-DD HH:MM", "notes": "Created by TARS"}
```

### Provider: mcp (any MCP calendar connector)

If provider is `mcp`, check `<mcp_servers>` at runtime for a calendar connector (e.g., Microsoft365, Google Calendar). Use the MCP tool's native operations. Map MCP operations to the category operations above.

---

## Tasks

category: tasks
required: true
status: configured
provider: remindctl
type: cli
operations:
  list: "remindctl list {list_name} --json"
  add: 'remindctl add --title "{title}" --list {list} --due {due} --notes "{notes}"'
  edit: 'remindctl edit {id} --title "{title}" --due {due}'
  complete: "remindctl complete {id}"
  delete: "remindctl delete {id} --force"
  overdue: "remindctl overdue --json"
config:
  lists: [Active, Delegated, Backlog]
constraints:
  - Person-named lists are read-only
  - Only create/edit/delete in Active, Delegated, Backlog
  - Parse notes defensively: missing fields = unknown, not error

### Provider: remindctl (Apple Reminders via CLI)

remindctl is a CLI tool for Apple Reminders.

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

### Provider: mcp (any MCP task connector)

If provider is `mcp`, check `<mcp_servers>` at runtime for a task connector (e.g., Todoist, Things, Microsoft To Do). Use the MCP tool's native operations. Map MCP operations to the category operations above.

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

Skills reference integration categories, not specific tools:

1. Read `reference/integrations.md`, find the relevant category section
2. Check `status` field:
   - `configured` → execute the operation using the provider's type (http-api, cli, or mcp)
   - `not_configured` → skip and note gap: "[Category] not configured. Run /welcome to set up."
   - `error` → report the specific error
3. For `mcp` type providers, check `<mcp_servers>` at runtime for available MCP tools
4. If a configured integration fails at runtime, fall back to workspace-only data and report the gap

### MCP discovery at runtime

For any category with `status: not_configured` or `type: mcp`:
1. Check `<mcp_servers>` context for matching MCP tools
2. If found, use the MCP tool's native operations
3. Map results to the category's expected output format

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

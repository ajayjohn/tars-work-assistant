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
recommended_provider: mcp
legacy_providers: eventlink (HTTP)

### Provider: MCP (Recommended for v2.1+)

**Configuration**: Add calendar MCP server to `.mcp.json`:

```json
{
  "mcpServers": {
    "calendar": {
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/your/calendar-mcp-server/index.js"],
      "env": {
        "CALENDAR_PROVIDER": "apple"
      }
    }
  }
}
```

**Note for user**: Replace `/path/to/your/calendar-mcp-server/index.js` with actual path to your built calendar MCP server.

**Operations**: TARS uses MCP server's native tools:
- `list_events` → Fetch events for date range
- `create_event` → Create new calendar event
- `get_event` → Get event details

**Skills usage**: Check `<mcp_servers>` context for calendar MCP server first. If found, use MCP tools directly. If not found, check for legacy eventlink configuration.

**Constraints**:
- Date format MUST be YYYY-MM-DD
- Always resolve relative dates before querying
- Only create events with no attendees
- Never update/delete events not created by TARS
- "Focus time" blocks count as available

### Provider: eventlink (Legacy - v2.0)

Eventlink is a local HTTP API for Apple Calendar.

**Configuration**:

```yaml
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
```

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

---

## Tasks

category: tasks
required: true
recommended_provider: mcp
legacy_providers: remindctl (CLI)

### Provider: MCP (Recommended for v2.1+)

**Configuration**: Add reminders MCP server to `.mcp.json`:

```json
{
  "mcpServers": {
    "reminders": {
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/your/reminders-mcp-server/index.js"],
      "env": {
        "REMINDERS_PROVIDER": "apple"
      }
    }
  }
}
```

**Note for user**: Replace `/path/to/your/reminders-mcp-server/index.js` with actual path to your built reminders MCP server.

**Operations**: TARS uses MCP server's native tools:
- `list_reminders` → Fetch tasks from list
- `create_reminder` → Create new task
- `complete_reminder` → Mark task complete

**Skills usage**: Check `<mcp_servers>` context for reminders MCP server first. If found, use MCP tools. If not found, check for legacy remindctl.

**Constraints**:
- Parse notes defensively: missing fields = unknown, not error
- Only create/edit/delete in allowed lists

### Provider: remindctl (Legacy - v2.0)

remindctl is a CLI tool for Apple Reminders.

**Configuration**:

```yaml
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
```

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

## Migration Guide: HTTP/CLI → MCP

### For Calendar (eventlink → MCP)

**Step 1**: Locate your calendar MCP server (already built)

**Step 2**: Update `.mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "calendar": {
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/your/calendar-mcp-server/index.js"],
      "env": {
        "CALENDAR_PROVIDER": "apple"
      }
    }
  }
}
```

**Step 3**: Restart Claude Desktop / Cowork

**Step 4**: Test: "What's on my calendar today?"

**Step 5**: Remove eventlink configuration from integrations.md once MCP works

### For Tasks (remindctl → MCP)

**Step 1**: Locate your reminders MCP server (already built)

**Step 2**: Update `.mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "reminders": {
      "type": "stdio",
      "command": "node",
      "args": ["/path/to/your/reminders-mcp-server/index.js"],
      "env": {
        "REMINDERS_PROVIDER": "apple"
      }
    }
  }
}
```

**Step 3**: Restart Claude Desktop / Cowork

**Step 4**: Test: "What's on my plate?" or "Create task: Review Q3 roadmap by Friday"

**Step 5**: Remove remindctl configuration from integrations.md once MCP works

### Testing Migration

After migration, test:
- **Calendar**: "What's on my calendar today?", "Am I free tomorrow?", "When did I last meet Sarah?"
- **Tasks**: "What's on my plate?", "Create task: Review Q3 roadmap by Friday"

All should work identically to HTTP/CLI integrations.

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

# KPI definitions

User-maintained file defining metrics per team and initiative. Used by `/performance-report` to determine what to measure and where to pull data.

Populated by `/bootstrap`. Add or modify metrics as your teams evolve.

---

## Example: Engineering team

- **Velocity**: Average story points completed per sprint (~~project tracker)
- **Cycle time**: Average days from In Progress to Done (~~project tracker)
- **Defect rate**: Bugs created / stories completed (~~project tracker)
- **Deployment frequency**: Releases per sprint (~~project tracker)

## Example: Data team

- **Pipeline reliability**: Data pipeline success rate (~~monitoring)
- **Data freshness**: Lag time from source to warehouse (~~monitoring)
- **Incident count**: Data quality incidents per sprint (~~project tracker)

## Example: Platform team

- **Uptime**: Platform availability percentage (~~monitoring)
- **Infrastructure cost**: Monthly cloud spend trend (billing)
- **Ticket resolution time**: Average time to resolve support tickets (~~project tracker)

---

## Example: Initiative A

- **Feature completion**: Done / Total stories (~~project tracker)
- **Blocked items**: Issues in Blocked status (~~project tracker)
- **Timeline adherence**: Actual vs planned milestone dates

---

## Adding new KPIs

1. Add under the appropriate team or initiative heading
2. Format: `- **Metric Name**: Description (data source)`
3. Include the data source in parentheses so the report protocol knows where to query
4. Use ~~connector placeholders for data sources (e.g., ~~project tracker, ~~monitoring)

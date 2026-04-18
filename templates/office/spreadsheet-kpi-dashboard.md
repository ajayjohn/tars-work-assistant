# {{title}} — KPI Dashboard

**Period:** {{period_start}} → {{period_end}}
**Audience:** {{audience}}
**Data warehouse:** {{data_warehouse_server}}

---

## Sheet 1: Summary

| Metric | Value | Target | Δ vs prior | Status |
|--------|-------|--------|-----------|--------|
| {{metric_1}} | {{value_1}} | {{target_1}} | {{delta_1}} | {{status_1}} |
| {{metric_2}} | {{value_2}} | {{target_2}} | {{delta_2}} | {{status_2}} |
| {{metric_3}} | {{value_3}} | {{target_3}} | {{delta_3}} | {{status_3}} |

Formatting hints for the render skill:
- Status column: conditional fill (green / yellow / red)
- Δ column: arrow icon + colored text

## Sheet 2: Trends

One time-series per KPI. Columns: `date`, `{{kpi_name}}`.

| date | {{kpi_name}} |
|------|--------------|
| {{date_1}} | {{value_1}} |
| {{date_2}} | {{value_2}} |

Add chart on this sheet: line chart, x=date, y={{kpi_name}}.

## Sheet 3: Segments (optional)

Break each KPI by segment — customer tier, region, product line, etc.

| segment | {{metric}} |
|---------|-----------|
| {{seg_1}} | {{seg_value_1}} |

## Sheet 4: Source queries

| Metric | Capability | Server | Query / path |
|--------|-----------|--------|--------------|
| {{metric_1}} | data-warehouse | {{dw_server}} | {{query_1}} |
| {{metric_2}} | analytics | {{analytics_server}} | {{path_2}} |

---

Render hints passed to the `xlsx` skill:
- Freeze row 1 of every sheet.
- Title row: brand primary color background, white bold text.
- Date columns: ISO 8601 format.

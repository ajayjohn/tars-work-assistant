---
tags:
  - tars/system
tars-created: 2026-03-21
---

# Schedule

## Recurring Scheduled Tasks

| Task | Schedule | Cron ID | Status |
|------|----------|---------|--------|
| Daily Briefing | (set during onboarding) | — | pending setup |
| Weekly Briefing | (set during onboarding) | — | pending setup |
| Maintenance | (set during onboarding) | — | pending setup |

## One-Time Scheduled Items

(Added by workflows as needed)

## Schedule Notes

- Cron IDs are stored in `housekeeping-state.yaml` after registration via CronCreate
- Briefings verify cron jobs are active at every session start
- If a cron job expires or fails, the briefing workflow re-registers it

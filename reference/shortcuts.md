# TARS shortcuts

This file documents the scheduling intent for TARS 3.0. The active runtime state for schedules and last-run bookkeeping lives in `_system/`.

## Daily maintenance

Recommended schedule:
- once per day
- usually late afternoon or end of workday

Suggested task description:

```text
Run the TARS daily maintenance pass.

1. Read _system/housekeeping-state.yaml.
2. If maintenance already ran today, exit cleanly.
3. Run scripts/archive.py against the active vault.
4. Run scripts/health-check.py against the active vault.
5. Run scripts/sync.py against the active vault.
6. Count items in inbox/pending/.
7. Update _system/housekeeping-state.yaml with last-run metadata.
8. If issues are detected, write a dated note or changelog entry in _system/changelog/ or journal/YYYY-MM/.

Constraints:
- Do not silently persist tasks or memory.
- Do not delete transcript archives.
- Do not require user interaction unless a blocking error occurs.
```

## Daily briefing

Recommended schedule:
- once each morning at the user’s preferred start time

Intent:
- create or present a daily briefing using calendar, tasks, and memory context

## Weekly briefing

Recommended schedule:
- once per week, usually Monday morning

Intent:
- summarize the previous week and orient the upcoming week

## Notes

- `/welcome` is the preferred place to register schedules when the environment supports it.
- Session-start checks should act as a fallback when scheduled execution is unavailable or stale.
- `_system/schedule.md` stores user-facing schedule preferences.

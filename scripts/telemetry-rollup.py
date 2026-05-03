#!/usr/bin/env python3
"""telemetry-rollup — aggregate _system/telemetry/*.jsonl over a window.

Stdlib-only. Pure (no writes). Two callers consume the output:

  - /briefing footer prints `--format text` on the configured weekly-rollup
    weekday (default Monday).
  - /maintain --weekly captures `--format json` and embeds the result in
    inbox/pending/weekly-review-YYYY-MM-DD.md alongside other proposals.

Aggregations:
  - per-skill event counts (skill_loaded, briefing_generated, meeting_processed,
    answer_delivered, lint_run, inbox_processed, sync_completed,
    archive_swept, maintenance_run)
  - vault-write counts grouped by destination (memory, journal, task, …)
  - retrieval-source mix from answer_delivered.source_hit_tier arrays
  - miss signals (events flagged with miss=true, plus answer_delivered
    where source_hit_tier is empty)
  - daily activity totals (event count per day in the window)

Contract:
  --vault <path>   required
  --days N         window size in days; default 7. Inclusive of today.
  --format text|json   default text
  --since YYYY-MM-DD   override window start (mutually exclusive with --days)
  --until YYYY-MM-DD   override window end
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telemetry-rollup")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--since", help="window start YYYY-MM-DD (overrides --days)")
    parser.add_argument("--until", help="window end YYYY-MM-DD (default today)")
    return parser


def _resolve_window(args: argparse.Namespace) -> tuple[date, date]:
    today = datetime.now().astimezone().date()
    end = date.fromisoformat(args.until) if args.until else today
    if args.since:
        start = date.fromisoformat(args.since)
    else:
        start = end - timedelta(days=max(args.days, 1) - 1)
    if start > end:
        raise SystemExit(f"error: --since {start} is after --until {end}")
    return start, end


def _iter_events(vault: Path, start: date, end: date):
    base = vault / "_system" / "telemetry"
    if not base.is_dir():
        return
    cur = start
    while cur <= end:
        path = base / f"{cur.isoformat()}.jsonl"
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            yield cur, json.loads(line)
                        except json.JSONDecodeError:
                            continue
            except OSError:
                pass
        cur += timedelta(days=1)


def _classify_vault_write(event: dict) -> str:
    """Bucket a vault_write event by destination prefix."""
    target = str(event.get("path") or event.get("file") or "")
    if target.startswith("memory/"):
        # second-level folder is the entity type
        parts = target.split("/", 2)
        if len(parts) >= 2:
            return f"memory/{parts[1]}"
        return "memory"
    if target.startswith("journal/"):
        return "journal"
    if target.startswith("inbox/"):
        return "inbox"
    if target.startswith("contexts/"):
        return "contexts"
    if target.startswith("archive/"):
        return "archive"
    if target.startswith("_system/"):
        return "_system"
    return "other"


def aggregate(vault: Path, start: date, end: date) -> dict[str, Any]:
    skill_events: Counter = Counter()
    vault_writes: Counter = Counter()
    daily_totals: Counter = Counter()
    source_tier_mix: Counter = Counter()
    miss_signals: Counter = Counter()
    skills_loaded: Counter = Counter()
    total_events = 0
    days_with_data: set[str] = set()

    for day, event in _iter_events(vault, start, end):
        total_events += 1
        day_str = day.isoformat()
        daily_totals[day_str] += 1
        days_with_data.add(day_str)
        event_type = str(event.get("event") or "")
        skill_events[event_type] += 1
        if event_type == "skill_loaded":
            name = str(event.get("skill") or event.get("name") or "")
            if name:
                skills_loaded[name] += 1
        elif event_type == "vault_write":
            vault_writes[_classify_vault_write(event)] += 1
        elif event_type == "answer_delivered":
            tiers = event.get("source_hit_tier")
            if isinstance(tiers, list):
                if not tiers:
                    miss_signals["answer_no_source"] += 1
                for t in tiers:
                    source_tier_mix[str(t)] += 1
        if event.get("miss") is True:
            miss_signals[event_type or "unknown"] += 1

    days_in_window = (end - start).days + 1
    return {
        "vault": str(vault),
        "window": {
            "since": start.isoformat(),
            "until": end.isoformat(),
            "days": days_in_window,
            "days_with_data": sorted(days_with_data),
        },
        "totals": {
            "events": total_events,
            "active_days": len(days_with_data),
        },
        "events_by_type": dict(skill_events.most_common()),
        "skills_loaded": dict(skills_loaded.most_common()),
        "vault_writes_by_destination": dict(vault_writes.most_common()),
        "retrieval_source_tier_mix": dict(source_tier_mix.most_common()),
        "miss_signals": dict(miss_signals.most_common()),
        "daily_event_totals": {d: daily_totals[d] for d in sorted(daily_totals)},
    }


def render_text(report: dict[str, Any]) -> str:
    w = report["window"]
    totals = report["totals"]
    lines: list[str] = []
    lines.append(
        f"Telemetry rollup — {w['since']} → {w['until']} "
        f"({w['days']}d, {totals['active_days']}d active, {totals['events']} events)"
    )
    if totals["events"] == 0:
        lines.append("  (no telemetry recorded in this window)")
        return "\n".join(lines)

    et = report["events_by_type"]
    if et:
        items = ", ".join(f"{name}={count}" for name, count in list(et.items())[:8])
        lines.append(f"  events: {items}")

    sl = report["skills_loaded"]
    if sl:
        items = ", ".join(f"/{name}×{count}" for name, count in list(sl.items())[:6])
        lines.append(f"  skills:  {items}")

    vw = report["vault_writes_by_destination"]
    if vw:
        items = ", ".join(f"{dest}={count}" for dest, count in list(vw.items())[:6])
        lines.append(f"  writes:  {items}")

    src = report["retrieval_source_tier_mix"]
    if src:
        items = ", ".join(f"{tier}={count}" for tier, count in list(src.items())[:6])
        lines.append(f"  sources: {items}")

    miss = report["miss_signals"]
    if miss:
        items = ", ".join(f"{name}={count}" for name, count in list(miss.items())[:6])
        lines.append(f"  misses:  {items}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3
    try:
        start, end = _resolve_window(args)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report = aggregate(vault, start, end)
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

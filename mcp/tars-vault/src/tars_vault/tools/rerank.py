"""rerank — deterministic score-based rerank of merged hybrid results.

Phase 4 implementation (PRD §6.5). PRD §6.5 notes an optional Haiku-backed
LLM rerank. Running that from inside the MCP server means calling the
Anthropic API with a key provisioned on the user's machine; until that wiring
lands we ship a deterministic score-based rerank with recency and tier boosts.
The orchestrating skill (`/answer`, `/meeting`) can still layer an LLM rerank
on top by spawning a sub-agent — that path is unaffected.

Arguments:
  candidates:   required list of result dicts (from fts_search / semantic_search)
                each with at least: {path, score | hybrid_score, source_type, date}.
  query:        optional string — reserved for a future LLM path; unused in
                the deterministic reranker beyond echoing in telemetry.
  top_k:        optional. Default 10. Hard-capped to 50.
  today:        optional "YYYY-MM-DD" for deterministic recency in tests.

Boosts (all applied multiplicatively over the hybrid score):
  * +1.15  same-day (date == today)
  * +1.10  within 7 days
  * +1.05  within 30 days
  * +1.10  source_type in {"transcript", "journal"} (evidence trail)

Returns:
  {"status": "ok", "results": [...ranked...], "count": N, "mode": "deterministic"}
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any


MAX_K = 50


def rerank(**kwargs: Any) -> dict:
    candidates = kwargs.get("candidates")
    if not isinstance(candidates, (list, tuple)):
        return {
            "status": "error",
            "results": [],
            "reason": "candidates must be a list of result dicts",
        }
    top_k = kwargs.get("top_k", 10)
    try:
        top_k = max(1, min(int(top_k), MAX_K))
    except (TypeError, ValueError):
        top_k = 10

    today_str = kwargs.get("today")
    today = _parse_date(today_str) if today_str else date.today()

    enriched: list[dict] = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        base = _base_score(row)
        boost = _recency_boost(row.get("date"), today) * _source_boost(row.get("source_type"))
        final = base * boost
        entry = dict(row)
        entry["rerank_score"] = final
        entry["rerank_boost"] = boost
        entry["rerank_base"] = base
        enriched.append(entry)

    enriched.sort(key=lambda r: r["rerank_score"], reverse=True)
    return {
        "status": "ok",
        "results": enriched[:top_k],
        "count": min(len(enriched), top_k),
        "mode": "deterministic",
    }


def _base_score(row: dict) -> float:
    for key in ("hybrid_score", "score"):
        value = row.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    distance = row.get("distance")
    if isinstance(distance, (int, float)):
        return 1.0 - float(distance)
    return 0.0


def _parse_date(value: str) -> date:
    year, month, day = value.split("-")
    return date(int(year), int(month), int(day))


def _recency_boost(date_str: str | None, today: date) -> float:
    if not date_str:
        return 1.0
    try:
        record_date = _parse_date(date_str)
    except (ValueError, AttributeError):
        return 1.0
    delta = today - record_date
    if delta < timedelta(days=0):
        return 1.0
    if delta <= timedelta(days=0):
        return 1.15
    if delta <= timedelta(days=7):
        return 1.10
    if delta <= timedelta(days=30):
        return 1.05
    return 1.0


def _source_boost(source_type: str | None) -> float:
    if source_type in ("transcript", "journal"):
        return 1.10
    return 1.0

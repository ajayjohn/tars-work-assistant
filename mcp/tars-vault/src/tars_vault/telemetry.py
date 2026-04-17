"""jsonl telemetry helper (PRD §26.11). Skeleton."""
import json, os
from datetime import datetime
from pathlib import Path


def append_event(vault: Path, event: dict) -> None:
    """Append a single event to ``_system/telemetry/YYYY-MM-DD.jsonl``."""
    if os.environ.get("TARS_DISABLE_TELEMETRY"):
        return
    day = datetime.now().astimezone().strftime("%Y-%m-%d")
    target = Path(vault) / "_system" / "telemetry" / f"{day}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")

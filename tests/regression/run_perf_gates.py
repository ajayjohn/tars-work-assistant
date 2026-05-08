"""Layer 6: performance gates.

SessionStart against a 200-note synthetic vault must complete in <300ms median
across 5 runs. Catches regressions where someone adds a slow per-session check.

Usage:
    python3 -m tests.regression.run_perf_gates [--base /tmp/tars-qa]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _scaffold_perf_vault(target: Path, n_notes: int = 200) -> None:
    """Build a synthetic 200-note vault under target/perf for benchmarking.

    Uses the s9-advanced scaffold as the seed (already includes 50 initiatives
    + Obsidian config) and pads with additional notes up to n_notes.
    """
    import shutil
    if target.exists():
        shutil.rmtree(target)
    scaffold_base = target / "_scaffold"
    scaffold_base.mkdir(parents=True)
    subprocess.run(
        [sys.executable, "-m", "tests.regression.scaffold_scenarios",
         "--base", str(scaffold_base)],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
    )
    s9_src = scaffold_base / "s9-advanced"
    if not s9_src.is_dir():
        raise RuntimeError("scaffold did not create s9-advanced")
    shutil.copytree(s9_src, target / "perf", dirs_exist_ok=True)
    notes_dir = target / "perf" / "memory" / "initiatives"
    notes_dir.mkdir(parents=True, exist_ok=True)
    existing = len(list(notes_dir.glob("*.md")))
    needed = max(0, n_notes - existing)
    for i in range(existing + 1, existing + needed + 1):
        (notes_dir / f"perf-{i}.md").write_text(
            '---\n'
            f'tars-summary: Perf {i}\n'
            'tars-status: active\n'
            'tars-owner: "[[X]]"\n'
            'tars-created: "2026-05-08"\n'
            'tars-modified: "2026-05-08"\n'
            'tags: [tars/initiative]\n'
            '---\n',
            encoding="utf-8",
        )


def _time_session_start(vault: Path) -> float:
    env = os.environ.copy()
    env["TARS_VAULT_PATH"] = str(vault)
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "hooks" / "session-start.py")],
        env=env, cwd=str(vault), input=b"",
        capture_output=True, timeout=60,
    )
    elapsed = time.perf_counter() - start
    if proc.returncode != 0:
        raise RuntimeError(f"session-start failed: rc={proc.returncode} "
                           f"stderr={proc.stderr.decode('utf-8', 'replace')[:200]}")
    return elapsed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/tmp/tars-qa-perf")
    ap.add_argument("--n-notes", type=int, default=200)
    ap.add_argument("--threshold-ms", type=float, default=300.0)
    ap.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()
    base = Path(args.base)
    _scaffold_perf_vault(base, n_notes=args.n_notes)
    vault = base / "perf"
    timings = [_time_session_start(vault) * 1000 for _ in range(args.runs)]
    median = statistics.median(timings)
    summary = {
        "layer": "perf",
        "vault_notes": args.n_notes,
        "runs": args.runs,
        "session_start_ms": {
            "median": round(median, 1),
            "min": round(min(timings), 1),
            "max": round(max(timings), 1),
            "all": [round(t, 1) for t in timings],
        },
        "threshold_ms": args.threshold_ms,
        "passed": median <= args.threshold_ms,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

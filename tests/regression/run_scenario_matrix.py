"""Run SessionStart against each PRD-18 scenario and assert expectations.

Each scenario has an expected substring (or `<<EMPTY>>`) the user should see
on first session. We reset the acknowledged_notices store before each run to
simulate "first session after this state was reached".

Usage:
    python3 -m tests.regression.run_scenario_matrix [--base /tmp/tars-qa]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAFFOLD_MODULE = "tests.regression.scaffold_scenarios"

# Each entry: (scenario, [substrings that MUST appear], [substrings that MUST NOT appear])
EXPECTATIONS: list[tuple[str, list[str], list[str]]] = [
    ("s1-empty",
     ["isn't a TARS workspace yet", "/welcome"],
     ["mcp__", "python3 scripts/", "cron"]),
    ("s2-fresh-headless",
     ["scheduled jobs aren't running", "/welcome --setup-schedules"],
     ["pending migration", "mcp__", "python3 scripts/", "cron",
      "_system/tools-registry.yaml", "step 7"]),
    ("s3-fresh-obsidian",
     ["scheduled jobs aren't running", "/welcome --setup-schedules"],
     ["pending migration", "mcp__", "python3 scripts/", "cron"]),
    ("s4-stale-version",
     ["TARS was upgraded", "No migration needed"],
     ["python3 scripts/", "cron", "step 7"]),
    ("s5-path-mismatch",
     ["does not match the recorded workspace", "/welcome --relocate"],
     ["mcp__", "python3 scripts/", "cron"]),
    ("s6-polluted-frontmatter",
     ["non-TARS frontmatter", "/lint --fix-prefixes"],
     ["mcp__", "python3 scripts/", "cron"]),
    ("s7-mid-mode-switch",
     ["scheduled jobs aren't running"],   # baseline: schedules notice
     ["mcp__", "python3 scripts/", "cron"]),
    ("s8-sparse-returning",
     ["Welcome back", "/briefing --catchup"],
     ["mcp__", "python3 scripts/", "cron"]),
    ("s9-advanced",
     ["active initiative(s) haven't been touched", "/lint --stale",
      "item(s) waiting in your inbox"],
     ["mcp__", "python3 scripts/", "cron"]),
]


def _strip_ack_store(install_yaml: Path) -> None:
    """Remove any `acknowledged_notices:` block so each run is "first session"."""
    if not install_yaml.is_file():
        return
    text = install_yaml.read_text(encoding="utf-8")
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        if line.startswith("acknowledged_notices"):
            in_block = True
            continue
        if in_block:
            if line and not (line.startswith(" ") or line.startswith("\t")):
                in_block = False
            else:
                continue
        out.append(line)
    install_yaml.write_text("\n".join(out) + ("\n" if out and out[-1] else ""),
                            encoding="utf-8")


def _run_session_start(vault: Path) -> str:
    env = os.environ.copy()
    env["TARS_VAULT_PATH"] = str(vault)
    env.pop("TARS_VAULT_WRITE_ANYWAY", None)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "hooks" / "session-start.py")],
        env=env, cwd=str(vault), input=b"",
        capture_output=True, timeout=60,
    )
    if proc.returncode != 0:
        return f"<<HOOK ERROR rc={proc.returncode}>>: {proc.stderr.decode('utf-8', 'replace')}"
    out = proc.stdout.decode("utf-8", "replace")
    try:
        data = json.loads(out)
        return data.get("hookSpecificOutput", {}).get("additionalContext", "")
    except json.JSONDecodeError:
        return f"<<NON-JSON>>: {out[:200]}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/tmp/tars-qa")
    ap.add_argument("--rescaffold", action="store_true",
                    help="Re-scaffold scenarios before running.")
    args = ap.parse_args()

    base = Path(args.base)
    if args.rescaffold or not base.is_dir():
        # Capture scaffold stdout so it doesn't pollute our matrix JSON.
        subprocess.run([sys.executable, "-m", SCAFFOLD_MODULE, "--base", str(base)],
                       cwd=str(REPO_ROOT), check=True,
                       stdout=subprocess.DEVNULL)

    results = []
    failed = 0
    for scenario, must_have, must_not_have in EXPECTATIONS:
        vault = base / scenario
        if not vault.is_dir():
            results.append({"scenario": scenario, "status": "missing",
                            "output": "", "violations": ["scenario directory not present"]})
            failed += 1
            continue
        _strip_ack_store(vault / "_system" / "install.yaml")
        out = _run_session_start(vault)
        violations = []
        for s in must_have:
            if s not in out:
                violations.append(f"missing required substring: {s!r}")
        for s in must_not_have:
            if s in out:
                violations.append(f"forbidden substring present: {s!r}")
        status = "pass" if not violations else "fail"
        if violations:
            failed += 1
        results.append({"scenario": scenario, "status": status,
                        "output": out, "violations": violations})

    summary = {
        "layer": "scenario_matrix",
        "scenarios_total": len(EXPECTATIONS),
        "passed": sum(1 for r in results if r["status"] == "pass"),
        "failed": failed,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

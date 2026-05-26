"""Deterministic stdlib-only MCP test runner.

Used by the regression suite when `pytest` is unavailable. It executes the
existing standalone test entrypoints in subprocesses instead of importing them
in-process, which keeps path and environment behavior aligned with the way the
tests are documented to run.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
FIXTURE_VAULT = TESTS / "fixtures" / "fixture-vault"


def _run_script(path: Path) -> int:
    env = os.environ.copy()
    env.setdefault("TARS_VAULT_PATH", str(FIXTURE_VAULT))
    print(f"==> {path.name}")
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode != 0:
        print(f"FAILED {path.name} (rc={proc.returncode})", file=sys.stderr)
    return proc.returncode


def main() -> int:
    for name in ("test_tools.py", "test_skeleton.py", "test_search_index.py"):
        rc = _run_script(TESTS / name)
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

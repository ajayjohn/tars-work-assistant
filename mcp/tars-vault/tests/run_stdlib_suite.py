"""Deterministic stdlib-only MCP test runner.

Used by the regression suite when `pytest` is unavailable. This avoids relying
on `unittest discover` behavior that can vary across environments while still
covering the intended MCP helper tests.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import test_search_index  # noqa: E402
import test_skeleton  # noqa: E402
import test_tools  # noqa: E402


def main() -> int:
    suite = unittest.TestLoader().loadTestsFromTestCase(test_tools.ToolTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if test_skeleton.run() != 0:
        return 1
    if test_search_index.run() != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

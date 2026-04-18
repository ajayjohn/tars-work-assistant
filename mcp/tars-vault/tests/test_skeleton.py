"""Smoke test for the Phase 1a skeleton.

Verifies the package imports cleanly and exposes the expected tool surface.
"""
import importlib


EXPECTED_TOOLS = {
    "append_note",
    "archive_note",
    "classify_file",
    "create_note",
    "detect_near_duplicates",
    "fts_search",
    "move_note",
    "read_note",
    "refresh_integrations",
    "rerank",
    "resolve_capability",
    "scan_secrets",
    "search_by_tag",
    "semantic_search",
    "update_frontmatter",
    "write_note_from_content",
}


def test_package_imports() -> None:
    pkg = importlib.import_module("tars_vault")
    assert pkg.__version__


def test_tool_surface_matches_expectation() -> None:
    tools = importlib.import_module("tars_vault.tools")
    assert set(tools.__all__) == EXPECTED_TOOLS


def run() -> int:
    test_package_imports()
    test_tool_surface_matches_expectation()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

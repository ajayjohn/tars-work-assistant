"""Smoke test for the Phase 1a skeleton.

Verifies the package imports cleanly and exposes the expected tool surface.
"""
import importlib
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "mcp" / "tars-vault" / "src"))


EXPECTED_TOOLS = {
    "append_note",
    "archive_candidates",
    "archive_note",
    "classify_file",
    "context_bundle",
    "context_gaps",
    "create_note",
    "detect_near_duplicates",
    "entity_timeline",
    "format_wikilink",
    "fts_search",
    "install_extension",
    "list_extensions",
    "move_note",
    "read_extension",
    "read_note",
    "read_system_file",
    "refresh_integrations",
    "rerank",
    "resolve_alias",
    "resolve_capability",
    "resolve_extension",
    "runtime_info",
    "scan_secrets",
    "scaffold_extension",
    "scaffold_workspace",
    "search_by_tag",
    "semantic_search",
    "update_frontmatter",
    "validate_extension",
    "workspace_map",
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

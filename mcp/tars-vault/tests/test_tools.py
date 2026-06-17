#!/usr/bin/env python3
"""Unit tests for tars-vault tool handlers (v3.1.1).

Stdlib-only. Creates a temp fixture vault, exercises the handlers, asserts
the returned dict shape + side effects. No network, no obsidian-cli required.

Run: python3 mcp/tars-vault/tests/test_tools.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "mcp" / "tars-vault" / "src"))

from tars_vault.tools.append_note import append_note
from tars_vault.tools.archive_candidates import archive_candidates
from tars_vault.tools.archive_note import archive_note
from tars_vault.tools.classify_file import classify_file
from tars_vault.tools.context_bundle import context_bundle
from tars_vault.tools.context_gaps import context_gaps
from tars_vault.tools.create_note import create_note
from tars_vault.tools.detect_near_duplicates import detect_near_duplicates
from tars_vault.tools.entity_timeline import entity_timeline
from tars_vault.tools.install_extension import install_extension
from tars_vault.tools.list_extensions import list_extensions
from tars_vault.tools.move_note import move_note
from tars_vault.tools.read_extension import read_extension
from tars_vault.tools.read_note import read_note
from tars_vault.tools.read_system_file import read_system_file
from tars_vault.tools.resolve_alias import resolve_alias
from tars_vault.tools.resolve_capability import resolve_capability
from tars_vault.tools.resolve_extension import resolve_extension
from tars_vault.tools.runtime_info import runtime_info
from tars_vault.tools.scan_secrets import scan_secrets
from tars_vault.tools.scaffold_extension import scaffold_extension
from tars_vault.tools.scaffold_workspace import scaffold_workspace
from tars_vault.tools.search_by_tag import search_by_tag
from tars_vault.tools.update_frontmatter import update_frontmatter
from tars_vault.tools.validate_extension import validate_extension
from tars_vault.tools.workspace_map import workspace_map
from tars_vault.tools.write_note_from_content import write_note_from_content
from tars_vault.server import _call_handler_sync


class ToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="tars-test-")
        self.vault = Path(self.tmp)
        (self.vault / "memory" / "people").mkdir(parents=True)
        (self.vault / "journal" / "2026-04").mkdir(parents=True)
        (self.vault / "_system").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _install_owned_tasks_extension(self, *, paths: str = "tasks/**", tags: str = "tars/task") -> None:
        ext_dir = self.vault / "extensions" / "tasks.airtable"
        ext_dir.mkdir(parents=True, exist_ok=True)
        (ext_dir / "extension.yaml").write_text(
            "id: tasks.airtable\n"
            "name: Airtable Tasks\n"
            "version: \"1.0.0\"\n"
            "tars_extension_version: \"1\"\n"
            "type: provider-adapter\n"
            "capabilities:\n"
            "  - tasks\n"
            "applies_to:\n"
            "  skills:\n"
            "    - tasks\n"
            "    - maintain\n"
            "entrypoints:\n"
            "  instructions: instructions.md\n"
            "  tool_contract: tool-contract.yaml\n"
            "safety:\n"
            "  requires_review: true\n"
            "  may_write_workspace: false\n"
            "  may_mutate_external_provider: false\n"
            "owns:\n"
            "  capabilities:\n"
            "    - tasks\n"
            "  workspace_paths:\n"
            f"    - {paths}\n"
            "  tags:\n"
            f"    - {tags}\n"
            "  provider_tools:\n"
            "    - mcp__airtable__.*\n"
            "  enforcement: fail_closed\n"
        )
        (ext_dir / "instructions.md").write_text("# Airtable Tasks\n")
        (ext_dir / "tool-contract.yaml").write_text("provider: airtable\n")
        (self.vault / "_system" / "extensions.yaml").write_text(
            "version: \"1\"\n"
            "extensions:\n"
            "  tasks.airtable:\n"
            "    enabled: true\n"
            "    source: local\n"
            "    root: workspace\n"
            "    path: extensions/tasks.airtable\n"
            "    installed_version: \"1.0.0\"\n"
        )

    # --- create / read / append / update ---

    def test_create_then_read_roundtrip(self) -> None:
        r = create_note(
            vault=str(self.vault),
            path="memory/people/alice.md",
            frontmatter={"tags": ["tars/person"], "tars-name": "Alice"},
            body="# Alice\n\nA test note.",
        )
        self.assertEqual(r["status"], "ok")
        r = read_note(vault=str(self.vault), file="memory/people/alice.md")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["frontmatter"]["tars-name"], "Alice")
        self.assertIn("Alice", r["body"])

    def test_scaffold_workspace_creates_first_run_structure(self) -> None:
        workspace = self.vault / "fresh"
        r = scaffold_workspace(
            vault=str(workspace),
            workspace_type="headless",
            user_name="Ajay",
            user_role="Product",
            company="Acme",
            persona="product-leader",
        )
        self.assertEqual(r["status"], "ok")
        for rel in [
            "inbox/pending",
            "inbox/processed",
            "memory/people",
            "memory/initiatives",
            "tasks",
            "journal",
            "archive/transcripts",
            "extensions",
        ]:
            self.assertTrue((workspace / rel).is_dir(), rel)
        self.assertTrue((workspace / "_system" / "activity-ledger.yaml").is_file())
        self.assertTrue((workspace / "_system" / "extensions.yaml").is_file())
        self.assertTrue((workspace / "index.md").is_file())
        index = (workspace / "index.md").read_text()
        self.assertIn("Slash commands are optional shortcuts", index)
        self.assertIn("Process everything in my inbox", index)
        config = (workspace / "_system" / "config.md").read_text()
        self.assertIn("tars-user-name: Ajay", config)
        install = (workspace / "_system" / "install.yaml").read_text()
        self.assertIn("workspace_type: headless", install)
        self.assertIn("persona: \"product-leader\"", install)
        for rel in ("knowledge", "projects", "research", "_views"):
            self.assertFalse((workspace / rel).exists(), rel)
        for rel in ("INBOX.md", "MEMORY.md", "PEOPLE.md", "INITIATIVES.md", "inbox.md"):
            self.assertFalse((workspace / rel).exists(), rel)

    def test_scaffold_workspace_obsidian_adds_views_only(self) -> None:
        workspace = self.vault / "fresh-obsidian"
        r = scaffold_workspace(
            vault=str(workspace),
            workspace_type="obsidian",
            user_name="Ajay",
            user_role="Product",
            company="Acme",
            persona="product-leader",
        )
        self.assertEqual(r["status"], "ok")
        self.assertTrue((workspace / "memory").is_dir())
        self.assertTrue((workspace / "inbox" / "pending").is_dir())
        self.assertTrue((workspace / "_views" / "inbox-pending.base").is_file())
        install = (workspace / "_system" / "install.yaml").read_text()
        self.assertIn("workspace_type: obsidian", install)
        self.assertIn("obsidian_enabled: true", install)
        for rel in ("knowledge", "projects", "research"):
            self.assertFalse((workspace / rel).exists(), rel)

    def test_create_rejects_existing_without_overwrite(self) -> None:
        p = self.vault / "memory" / "people" / "bob.md"
        p.write_text("---\ntags: [tars/person]\n---\nexisting\n")
        r = create_note(
            vault=str(self.vault),
            path="memory/people/bob.md",
            frontmatter={"tags": ["tars/person"]},
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("already exists", r["reason"])

    def test_create_rejects_non_tars_key(self) -> None:
        r = create_note(
            vault=str(self.vault),
            path="memory/people/carol.md",
            frontmatter={"tags": ["tars/person"], "random_key": "x"},
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("not tars-prefixed", r["reason"])

    def test_append_chunked(self) -> None:
        p = self.vault / "journal" / "2026-04" / "note.md"
        p.write_text("initial\n")
        long_content = "x" * 100_000
        r = append_note(
            vault=str(self.vault),
            file="journal/2026-04/note.md",
            content=long_content,
            chunk_size=40_000,
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["bytes_appended"], 100_000)
        self.assertEqual(r["chunks"], 3)  # 40k + 40k + 20k

    def test_update_frontmatter_adds_removes(self) -> None:
        (self.vault / "memory" / "people" / "dan.md").write_text(
            "---\ntags: [tars/person]\ntars-role: Eng\n---\nbody\n"
        )
        r = update_frontmatter(
            vault=str(self.vault),
            file="memory/people/dan.md",
            updates={"tars-role": "Director", "tars-created": "2026-04-01"},
        )
        self.assertEqual(r["status"], "ok")
        self.assertIn("tars-role", r["updated"])
        self.assertIn("tars-created", r["updated"])
        r2 = read_note(vault=str(self.vault), file="memory/people/dan.md")
        self.assertEqual(r2["frontmatter"]["tars-role"], "Director")
        r = update_frontmatter(
            vault=str(self.vault),
            file="memory/people/dan.md",
            property="tars-title",
            value="Staff Engineer",
        )
        self.assertEqual(r["status"], "ok")
        self.assertIn("tars-title", r["updated"])
        # Now remove
        r = update_frontmatter(
            vault=str(self.vault),
            file="memory/people/dan.md",
            updates={"tars-created": None},
        )
        self.assertEqual(r["status"], "ok")
        self.assertIn("tars-created", r["removed"])

    def test_resolve_alias_default_and_context_override(self) -> None:
        (self.vault / "_system" / "alias-registry.md").write_text(
            "## Ambiguous Names\n"
            "| Short Name | Default Resolution | Context Override |\n"
            "|---|---|---|\n"
            "| Sam | [[Sam Product]] | security -> [[Sam Security]] |\n"
            "\n"
            "## Product Abbreviations\n"
            "| Abbreviation | Canonical |\n"
            "|---|---|\n"
            "| DP | [[Data Platform]] |\n"
        )
        r = resolve_alias(vault=str(self.vault), name="Sam")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["resolution_status"], "resolved")
        self.assertEqual(r["canonical"], "Sam Product")
        r = resolve_alias(vault=str(self.vault), name="Sam", context="security launch")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["canonical"], "Sam Security")
        r = resolve_alias(vault=str(self.vault), name="DP", kind="product")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["canonical"], "Data Platform")

    def test_runtime_info_reports_helper_state_without_mutation(self) -> None:
        r = runtime_info(vault=str(self.vault))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["helper"], "connected")
        self.assertIn("checks", r)

    # --- search / classify / dedupe ---

    def test_search_by_tag(self) -> None:
        (self.vault / "memory" / "people" / "e.md").write_text(
            "---\ntags: [tars/person, tars/vip]\ntars-role: Eng\n---\nAlice owns search.\n"
        )
        (self.vault / "memory" / "people" / "f.md").write_text(
            "---\ntags: [tars/vendor]\n---\n"
        )
        r = search_by_tag(vault=str(self.vault), tag="tars/person")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["count"], 1)

    def test_search_by_tag_query_and_frontmatter_filters(self) -> None:
        (self.vault / "memory" / "initiatives").mkdir(parents=True)
        (self.vault / "memory" / "initiatives" / "search.md").write_text(
            "---\n"
            "tags: [tars/initiative]\n"
            "tars-status: active\n"
            "tars-date: 2026-04-15\n"
            "---\n"
            "Search quality launch plan.\n"
        )
        (self.vault / "memory" / "initiatives" / "archive.md").write_text(
            "---\n"
            "tags: [tars/initiative]\n"
            "tars-status: paused\n"
            "tars-date: 2026-01-01\n"
            "---\n"
            "Legacy cleanup.\n"
        )
        r = search_by_tag(
            vault=str(self.vault),
            tag="tars/initiative",
            query="quality",
            frontmatter={"tars-status": "active", "tars-date__gte": "2026-04-01"},
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["count"], 1)
        self.assertEqual(r["results"][0]["path"], "memory/initiatives/search.md")

    def test_workspace_navigation_tools(self) -> None:
        stale_day = (date.today() - timedelta(days=60)).isoformat()
        overdue_day = (date.today() - timedelta(days=3)).isoformat()
        (self.vault / "memory" / "initiatives").mkdir(parents=True, exist_ok=True)
        (self.vault / "tasks").mkdir(parents=True, exist_ok=True)
        (self.vault / "archive" / "transcripts" / "2026-05").mkdir(parents=True, exist_ok=True)
        (self.vault / "inbox" / "pending").mkdir(parents=True, exist_ok=True)
        (self.vault / "inbox" / "pending" / "raw.txt").write_text("loose context")
        (self.vault / "memory" / "people" / "alice.md").write_text(
            "---\ntags: [tars/person]\ntars-name: Alice\ntars-modified: 2026-05-01\n---\nAlice owns search.\n"
        )
        (self.vault / "memory" / "initiatives" / "search.md").write_text(
            f"---\ntags: [tars/initiative]\ntars-status: active\ntars-modified: {stale_day}\n---\nSearch quality with [[Alice]].\n"
        )
        (self.vault / "tasks" / "follow-up.md").write_text(
            f"---\ntags: [tars/task]\ntars-status: open\ntars-due: {overdue_day}\n---\nFollow up with [[Alice]].\n"
        )
        (self.vault / "journal" / "2026-04" / "note.md").write_text(
            "---\ntags: [tars/journal]\ntars-date: 2026-05-02\n---\nSearch launch discussion with Alice.\n"
        )
        (self.vault / "archive" / "transcripts" / "2026-05" / "call.md").write_text(
            "---\ntags: [tars/transcript]\ntars-date: 2026-05-03\n---\nAlice mentioned search relevance.\n"
        )

        r = workspace_map(vault=str(self.vault), limit=5)
        self.assertEqual(r["status"], "ok")
        self.assertGreaterEqual(r["active_file_count"], 4)
        self.assertEqual(r["initiatives"]["active_count"], 1)
        self.assertEqual(r["tasks"]["overdue_count"], 1)
        self.assertTrue((self.vault / "_system" / "activity-ledger.yaml").is_file())

        gaps = context_gaps(vault=str(self.vault))
        self.assertEqual(gaps["status"], "ok")
        gap_types = {item["type"] for item in gaps["gaps"]}
        self.assertIn("pending_inbox", gap_types)
        self.assertIn("overdue_tasks", gap_types)
        self.assertIn("stale_active_initiatives", gap_types)

        timeline = entity_timeline(vault=str(self.vault), query="Alice", limit=10)
        self.assertEqual(timeline["status"], "ok")
        self.assertGreaterEqual(timeline["count"], 3)

        bundle = context_bundle(vault=str(self.vault), query="search", limit=5)
        self.assertEqual(bundle["status"], "ok")
        self.assertGreaterEqual(len(bundle["timeline"]), 2)

        candidates = archive_candidates(vault=str(self.vault), check="inbox")
        self.assertEqual(candidates["status"], "ok")
        self.assertIn("summary", candidates)

    def test_classify_file_resume(self) -> None:
        (self.vault / "contexts").mkdir()
        p = self.vault / "contexts" / "Alice Resume.md"
        p.write_text("cv body")
        r = classify_file(vault=str(self.vault), path="contexts/Alice Resume.md")
        self.assertEqual(r["status"], "ok")
        self.assertIn("people", r["proposed"])
        self.assertGreaterEqual(r["confidence"], 0.8)

    def test_detect_near_duplicates(self) -> None:
        (self.vault / "contexts").mkdir()
        (self.vault / "contexts" / "a.md").write_text("---\n---\nsame body\n")
        (self.vault / "contexts" / "b.md").write_text("---\n---\nsame body\n")
        r = detect_near_duplicates(vault=str(self.vault), folder="contexts")
        self.assertEqual(r["status"], "ok")
        self.assertGreaterEqual(r["cluster_count"], 1)

    # --- move / archive ---

    def test_move_note_rewrites_wikilinks(self) -> None:
        (self.vault / "memory" / "people" / "g.md").write_text(
            "---\ntags: [tars/person]\n---\ncontent\n"
        )
        (self.vault / "journal" / "2026-04" / "ref.md").write_text(
            "See [[memory/people/g]] and [[memory/people/g|G]]\n"
        )
        r = move_note(
            vault=str(self.vault),
            src="memory/people/g.md",
            dst="memory/people/archived/g.md",
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["references_rewritten"], 2)
        ref = (self.vault / "journal" / "2026-04" / "ref.md").read_text()
        self.assertIn("[[memory/people/archived/g]]", ref)
        self.assertIn("[[memory/people/archived/g|G]]", ref)

    def test_archive_note_refuses_decision_without_force(self) -> None:
        (self.vault / "memory" / "decisions").mkdir(parents=True)
        (self.vault / "memory" / "decisions" / "d.md").write_text(
            "---\ntags: [tars/decision]\n---\nbody\n"
        )
        r = archive_note(vault=str(self.vault), file="memory/decisions/d.md")
        self.assertEqual(r["status"], "error")
        self.assertIn("durable tag", r["reason"])

    def test_archive_note_refuses_recent_backlink_and_active_task(self) -> None:
        (self.vault / "memory" / "people" / "ivy.md").write_text(
            "---\ntags: [tars/person]\naliases: [Ivy]\n---\nbody\n"
        )
        (self.vault / "journal" / "2026-04" / "ref.md").write_text(
            "---\ntags: [tars/journal]\n---\nDiscussed [[Ivy]].\n"
        )
        (self.vault / "memory" / "tasks").mkdir(parents=True)
        (self.vault / "memory" / "tasks" / "task.md").write_text(
            "---\ntags: [tars/task]\ntars-status: open\n---\nFollow up with [[Ivy]].\n"
        )
        r = archive_note(vault=str(self.vault), file="memory/people/ivy.md")
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])
        types = {item["type"] for item in r["guardrails"]}
        self.assertIn("recent_backlink", types)
        self.assertIn("active_task_reference", types)

    def test_archive_note_dry_run_uses_typed_destination(self) -> None:
        (self.vault / "memory" / "people" / "old.md").write_text(
            "---\ntags: [tars/person]\ntars-modified: 2020-01-01\n---\nbody\n"
        )
        r = archive_note(vault=str(self.vault), file="memory/people/old.md", dry_run=True)
        self.assertEqual(r["status"], "ok")
        self.assertIn("archive/people/", r["to_path"])

    def test_archive_candidates_protect_legacy_tasks_and_pinned_notes(self) -> None:
        (self.vault / "memory" / "tasks").mkdir(parents=True, exist_ok=True)
        (self.vault / "tasks").mkdir(parents=True, exist_ok=True)
        (self.vault / "memory" / "people" / "old-ivy.md").write_text(
            "---\n"
            "tags: [tars/person]\n"
            "aliases: [Ivy]\n"
            "tars-staleness: ephemeral\n"
            "tars-modified: 2020-01-01\n"
            "---\n"
            "Old profile.\n"
        )
        (self.vault / "memory" / "people" / "pinned.md").write_text(
            "---\n"
            "tags: [tars/person]\n"
            "tars-pinned: true\n"
            "tars-staleness: ephemeral\n"
            "tars-modified: 2020-01-01\n"
            "---\n"
            "Pinned profile.\n"
        )
        (self.vault / "memory" / "tasks" / "legacy.md").write_text(
            "---\ntags: [tars/task]\ntars-status: open\n---\nFollow up with [[Ivy]].\n"
        )
        (self.vault / "tasks" / "current.md").write_text(
            "---\ntags: [tars/task]\ntars-status: open\n---\nAlso check [[memory/people/old-ivy]].\n"
        )
        r = archive_candidates(vault=str(self.vault), check="memory")
        self.assertEqual(r["status"], "ok")
        protected = {item["file"]: item for item in r["memory"]["protected"]}
        self.assertIn("memory/people/old-ivy.md", protected)
        reasons = protected["memory/people/old-ivy.md"]["protection_reasons"]
        self.assertIn("referenced by active task", reasons)
        self.assertGreaterEqual(r["memory"]["pinned_skipped"], 1)

    # --- integrations ---

    def test_resolve_capability_unresolved_without_registry(self) -> None:
        r = resolve_capability(vault=str(self.vault), capability="calendar")
        self.assertEqual(r["status"], "unresolved")

    def test_resolve_capability_finds_connected_server(self) -> None:
        (self.vault / "_system" / "integrations.md").write_text(
            "---\ntars-config-version: '2.0'\n---\n\n```yaml\n"
            "capabilities:\n"
            "  calendar: { preferred: [workiq], required: true }\n"
            "```\n"
        )
        (self.vault / "_system" / "tools-registry.yaml").write_text(
            "discovered_at: 2026-04-18T00:00:00-05:00\n"
            "ttl_hours: 24\n"
            "mcp_servers:\n"
            "  workiq:\n"
            "    status: connected\n"
            "    capabilities_provided: [calendar]\n"
            "    tools: []\n"
        )
        r = resolve_capability(vault=str(self.vault), capability="calendar")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["server"], "workiq")

    # --- extensions ---

    def test_scaffold_extension_registers_workspace_extension(self) -> None:
        r = scaffold_extension(
            vault=str(self.vault),
            extension_id="meeting-recording.example",
            name="Example Recording Adapter",
            type="provider-adapter",
            capability="meeting-recording",
            skills=["maintain", "meeting"],
            modes=["inbox", "sync"],
            enable=True,
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["path"], "extensions/meeting-recording.example")
        registry = (self.vault / "_system" / "extensions.yaml").read_text()
        self.assertIn("root: workspace", registry)
        self.assertIn("path: extensions/meeting-recording.example", registry)

        listed = list_extensions(vault=str(self.vault))
        self.assertEqual(listed["status"], "ok")
        self.assertEqual(len(listed["extensions"]), 1)
        self.assertTrue(listed["extensions"][0]["valid"])

        resolved = resolve_extension(
            vault=str(self.vault),
            skill="maintain",
            mode="inbox",
            capability="meeting-recording",
        )
        self.assertEqual(resolved["status"], "ok")
        self.assertEqual(resolved["selected"]["id"], "meeting-recording.example")
        self.assertEqual(resolved["selected"]["root"], "workspace")

        read = read_extension(vault=str(self.vault), extension_id="meeting-recording.example")
        self.assertEqual(read["status"], "ok")
        self.assertIn("Example Recording Adapter", read["content"])

        valid = validate_extension(vault=str(self.vault), extension_id="meeting-recording.example")
        self.assertEqual(valid["status"], "ok")
        self.assertTrue(valid["valid"])

    def test_validate_extension_rejects_plugin_root_path(self) -> None:
        (self.vault / "_system" / "extensions.yaml").write_text(
            "version: \"1\"\n"
            "extensions:\n"
            "  bad.plugin:\n"
            "    enabled: true\n"
            "    source: catalog\n"
            "    root: workspace\n"
            "    path: /tmp/plugin/extensions/bad.plugin\n"
        )
        r = list_extensions(vault=str(self.vault))
        self.assertEqual(r["status"], "ok")
        self.assertFalse(r["extensions"][0]["valid"])
        self.assertIn("workspace-relative", r["extensions"][0]["errors"][0])
        read = read_extension(vault=str(self.vault), extension_id="bad.plugin")
        self.assertEqual(read["status"], "error")

    def test_install_extension_copies_source_into_workspace(self) -> None:
        source = self.vault / "source-extension"
        source.mkdir()
        (source / "extension.yaml").write_text(
            "id: meeting-recording.catalog-demo\n"
            "name: Catalog Demo\n"
            "version: \"1.0.0\"\n"
            "tars_extension_version: \"1\"\n"
            "type: provider-adapter\n"
            "capabilities:\n"
            "  - meeting-recording\n"
            "applies_to:\n"
            "  skills:\n"
            "    - maintain\n"
            "  modes:\n"
            "    - inbox\n"
            "entrypoints:\n"
            "  instructions: instructions.md\n"
            "safety:\n"
            "  requires_review: true\n"
            "  may_write_workspace: false\n"
            "  may_mutate_external_provider: false\n"
        )
        (source / "instructions.md").write_text("# Catalog Demo\n")
        r = install_extension(
            vault=str(self.vault),
            source_path=str(source),
            source="catalog",
            enable=True,
        )
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["path"], "extensions/meeting-recording.catalog-demo")
        self.assertTrue((self.vault / "extensions" / "meeting-recording.catalog-demo" / "extension.yaml").is_file())
        registry = (self.vault / "_system" / "extensions.yaml").read_text()
        self.assertIn("source: catalog", registry)
        self.assertNotIn(str(source), registry)

    def test_server_exposes_extension_tools_and_rejects_unknown_args(self) -> None:
        r = _call_handler_sync("list_extensions", {"vault": str(self.vault)}, "")
        self.assertEqual(r["status"], "ok")
        bad = _call_handler_sync("list_extensions", {"vault": str(self.vault), "plugin_root": "/tmp/plugin"}, "")
        self.assertEqual(bad["status"], "error")
        self.assertIn("unknown argument", bad["reason"])

    # --- secrets ---

    def test_scan_secrets_detects_patterns(self) -> None:
        # Match the real-vault convention: single-quoted patterns, literal
        # backslashes (no YAML escaping).
        (self.vault / "_system" / "guardrails.yaml").write_text(
            "block_patterns:\n"
            "  - name: ssn\n"
            "    pattern: '\\d{3}-\\d{2}-\\d{4}'\n"
            "warn_patterns:\n"
            "  - name: salary\n"
            "    pattern: 'salary'\n"
        )
        r = scan_secrets(vault=str(self.vault), content="SSN 123-45-6789 please")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["classification"], "block")
        r = scan_secrets(vault=str(self.vault), content="re: salary review")
        self.assertEqual(r["classification"], "warn")
        r = scan_secrets(vault=str(self.vault), content="nothing to see here")
        self.assertEqual(r["classification"], "clean")

    def test_scan_secrets_blocks_common_tokens(self) -> None:
        shutil.copy(REPO / "_system" / "guardrails.yaml", self.vault / "_system" / "guardrails.yaml")
        samples = {
            "slack_bot_token": "xoxb-1234567890-abcdef0123456",
            "github_pat": "ghp_" + "A" * 36,
            "stripe_secret": "sk_live_" + "A" * 24,
            "twilio_account_sid": "AC" + "f" * 32,
            "sendgrid_api_key": "SG." + "a" * 22 + "." + "b" * 43,
            "google_api_key": "AIza" + "z" * 35,
            "openai_api_key": "sk-" + "A" * 24,
            "anthropic_api_key": "sk-ant-api03-" + "A" * 30,
        }
        for name, sample in samples.items():
            r = scan_secrets(vault=str(self.vault), content=f"key {sample}")
            self.assertEqual(r["classification"], "block", name)
            self.assertIn(name, {hit["name"] for hit in r["hits"]})
        r = scan_secrets(vault=str(self.vault), content="just a normal sentence with sk- in it")
        self.assertNotEqual(r["classification"], "block")

    # --- write_note_from_content is an alias ---

    def test_write_note_from_content_alias(self) -> None:
        r = write_note_from_content(
            vault=str(self.vault),
            path="memory/people/h.md",
            frontmatter={"tags": ["tars/person"]},
            body="x",
        )
        self.assertEqual(r["status"], "ok")

    def test_write_note_from_content_accepts_content_blob(self) -> None:
        blob = "---\ntars-summary: hi\n---\nbody text\n"
        r = _call_handler_sync(
            "write_note_from_content",
            {"vault": str(self.vault), "path": "memory/free.md", "content": blob},
            "",
        )
        self.assertEqual(r["status"], "ok")
        written = (self.vault / "memory" / "free.md").read_text()
        self.assertIn("tars-summary: hi", written)
        self.assertIn("body text", written)
        self.assertGreater((self.vault / "memory" / "free.md").stat().st_size, 0)

    def test_write_note_from_content_rejects_blob_and_split_args(self) -> None:
        r = _call_handler_sync(
            "write_note_from_content",
            {
                "vault": str(self.vault),
                "path": "memory/free.md",
                "content": "body",
                "frontmatter": {"tars-summary": "x"},
            },
            "",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("either content or frontmatter/body", r["reason"])

    def test_extension_owned_path_blocks_local_create(self) -> None:
        self._install_owned_tasks_extension()
        r = create_note(
            vault=str(self.vault),
            path="tasks/local-task.md",
            frontmatter={"tags": ["tars/task"], "tars-status": "open"},
            body="Local task should not be created.",
        )
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])
        self.assertEqual(r["extension_id"], "tasks.airtable")
        self.assertIn("fail_closed", r["reason"])
        self.assertFalse((self.vault / "tasks" / "local-task.md").exists())

    def test_extension_owned_tag_blocks_local_create_outside_path(self) -> None:
        self._install_owned_tasks_extension(paths="archive/tasks/**")
        r = create_note(
            vault=str(self.vault),
            path="contexts/task-candidate.md",
            frontmatter={"tags": ["tars/task"], "tars-status": "open"},
            body="A task by tag still belongs to the extension.",
        )
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])
        self.assertIn("tag:tars/task", r["matched_by"])

    def test_extension_owned_existing_note_blocks_append_update_move_archive(self) -> None:
        self._install_owned_tasks_extension()
        task = self.vault / "tasks" / "owned.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text("---\ntags: [tars/task]\ntars-status: open\n---\nbody\n")

        r = append_note(vault=str(self.vault), file="tasks/owned.md", content="more")
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])

        r = update_frontmatter(
            vault=str(self.vault),
            file="tasks/owned.md",
            updates={"tars-status": "done"},
        )
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])

        r = move_note(vault=str(self.vault), src="tasks/owned.md", dst="tasks/moved-owned.md")
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])

        r = archive_note(vault=str(self.vault), file="tasks/owned.md", force=True)
        self.assertEqual(r["status"], "error")
        self.assertTrue(r["blocked"])

    def test_dispatcher_rejects_unknown_args(self) -> None:
        r = _call_handler_sync(
            "create_note",
            {
                "vault": str(self.vault),
                "path": "memory/people/extra.md",
                "frontmatter": {"tags": ["tars/person"]},
                "body": "x",
                "garbage": "x",
            },
            "",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("unknown argument", r["reason"])

    def test_dispatcher_fails_closed_without_vault_signal(self) -> None:
        cwd = Path.cwd()
        old_env = os.environ.pop("TARS_VAULT_PATH", None)
        try:
            os.chdir(self.vault)
            r = _call_handler_sync("read_note", {"file": "missing"}, "")
        finally:
            os.chdir(cwd)
            if old_env is not None:
                os.environ["TARS_VAULT_PATH"] = old_env
        self.assertEqual(r["status"], "error")
        self.assertIn("does not know which workspace", r["reason"])

    def test_write_blocked_when_install_record_mismatches(self) -> None:
        (self.vault / "_system" / "install.yaml").write_text(
            'workspace_path: "/tmp/somewhere-else"\n'
        )
        r = _call_handler_sync(
            "create_note",
            {
                "vault": str(self.vault),
                "path": "memory/blocked.md",
                "frontmatter": {"tags": ["tars/person"]},
                "body": "x",
            },
            "",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("does not match", r["reason"])
        self.assertFalse((self.vault / "memory" / "blocked.md").exists())

    def test_read_allowed_when_install_record_mismatches(self) -> None:
        (self.vault / "_system" / "install.yaml").write_text(
            'workspace_path: "/tmp/somewhere-else"\n'
        )
        r = _call_handler_sync(
            "read_note",
            {"vault": str(self.vault), "file": "missing"},
            "",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("not found", r["reason"])

    def test_protected_paths_block_direct_write_tools(self) -> None:
        r = create_note(
            vault=str(self.vault),
            path="_system/install.md",
            frontmatter={"tags": ["tars/system"]},
            body="x",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("managed by TARS", r["reason"])
        (self.vault / "_system" / "config.md").write_text("---\ntags: [tars/system]\n---\n")
        r = update_frontmatter(
            vault=str(self.vault),
            file="_system/config.md",
            updates={"tars-summary": "x"},
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("managed by TARS", r["reason"])

    def test_read_system_file_parses_yaml(self) -> None:
        (self.vault / "_system" / "sample.yaml").write_text("alpha: 1\nitems: [a, b]\n")
        r = read_system_file(vault=str(self.vault), file="sample.yaml")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["data"]["alpha"], 1)
        self.assertEqual(r["data"]["items"], ["a", "b"])

    def test_create_note_schema_validation(self) -> None:
        shutil.copy(REPO / "_system" / "schemas.yaml", self.vault / "_system" / "schemas.yaml")
        r = create_note(
            vault=str(self.vault),
            path="memory/people/schema-missing.md",
            frontmatter={"tags": ["tars/person"], "tars-summary": "x"},
            body="x",
        )
        self.assertEqual(r["status"], "error")
        self.assertIn("tars-staleness", r["reason"])
        r = create_note(
            vault=str(self.vault),
            path="memory/people/schema-ok.md",
            frontmatter={
                "tags": ["tars/person"],
                "tars-summary": "x",
                "tars-staleness": "durable",
                "tars-created": "2026-05-07",
                "tars-modified": "2026-05-07",
            },
            body="x",
        )
        self.assertEqual(r["status"], "ok")

    def test_create_note_schema_validate_false_escape_hatch(self) -> None:
        shutil.copy(REPO / "_system" / "schemas.yaml", self.vault / "_system" / "schemas.yaml")
        r = create_note(
            vault=str(self.vault),
            path="memory/people/schema-skip.md",
            frontmatter={"tags": ["tars/person"], "tars-summary": "x"},
            body="x",
            validate=False,
        )
        self.assertEqual(r["status"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)

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
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "mcp" / "tars-vault" / "src"))

from tars_vault.tools.append_note import append_note
from tars_vault.tools.archive_note import archive_note
from tars_vault.tools.classify_file import classify_file
from tars_vault.tools.create_note import create_note
from tars_vault.tools.detect_near_duplicates import detect_near_duplicates
from tars_vault.tools.move_note import move_note
from tars_vault.tools.read_note import read_note
from tars_vault.tools.resolve_capability import resolve_capability
from tars_vault.tools.scan_secrets import scan_secrets
from tars_vault.tools.search_by_tag import search_by_tag
from tars_vault.tools.update_frontmatter import update_frontmatter
from tars_vault.tools.write_note_from_content import write_note_from_content


class ToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="tars-test-")
        self.vault = Path(self.tmp)
        (self.vault / "memory" / "people").mkdir(parents=True)
        (self.vault / "journal" / "2026-04").mkdir(parents=True)
        (self.vault / "_system").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

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
        # Now remove
        r = update_frontmatter(
            vault=str(self.vault),
            file="memory/people/dan.md",
            updates={"tars-created": None},
        )
        self.assertEqual(r["status"], "ok")
        self.assertIn("tars-created", r["removed"])

    # --- search / classify / dedupe ---

    def test_search_by_tag(self) -> None:
        (self.vault / "memory" / "people" / "e.md").write_text(
            "---\ntags: [tars/person, tars/vip]\n---\n"
        )
        (self.vault / "memory" / "people" / "f.md").write_text(
            "---\ntags: [tars/vendor]\n---\n"
        )
        r = search_by_tag(vault=str(self.vault), tag="tars/person")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["count"], 1)

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

    # --- write_note_from_content is an alias ---

    def test_write_note_from_content_alias(self) -> None:
        r = write_note_from_content(
            vault=str(self.vault),
            path="memory/people/h.md",
            frontmatter={"tags": ["tars/person"]},
            body="x",
        )
        self.assertEqual(r["status"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Real-world smoke checks for a fresh TARS workspace.

This is intentionally cheap and deterministic. It exercises the same MCP tool
path that /welcome depends on, then verifies that the first-run user surface is
actually usable: folders exist, index.md exists, writes land in the workspace,
and search/read operations work without Obsidian.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mcp" / "tars-vault" / "src"))

from tars_vault.tools.create_note import create_note
from tars_vault.tools.append_note import append_note
from tars_vault.tools.archive_note import archive_note
from tars_vault.tools.classify_file import classify_file
from tars_vault.tools.detect_near_duplicates import detect_near_duplicates
from tars_vault.tools.fts_search import fts_search
from tars_vault.tools.move_note import move_note
from tars_vault.tools.read_note import read_note
from tars_vault.tools.scaffold_workspace import scaffold_workspace
from tars_vault.tools.scan_secrets import scan_secrets
from tars_vault.tools.search_by_tag import search_by_tag
from tars_vault.tools.semantic_search import semantic_search
from tars_vault.tools.update_frontmatter import update_frontmatter


class FreshInstallSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="tars-real-world-")
        self.workspace = Path(self.tmp) / "TARS Workspace"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fresh_headless_setup_is_usable(self) -> None:
        result = scaffold_workspace(
            vault=str(self.workspace),
            workspace_type="headless",
            user_name="Ajay",
            user_role="Product Leader",
            company="Acme",
            persona="product-leader",
        )
        self.assertEqual(result["status"], "ok", result)

        expected_dirs = [
            "inbox/pending",
            "inbox/processed",
            "memory/people",
            "memory/vendors",
            "memory/competitors",
            "memory/products",
            "memory/initiatives",
            "memory/decisions",
            "memory/org-context",
            "journal",
            "contexts/artifacts",
            "archive/transcripts",
        ]
        for rel in expected_dirs:
            self.assertTrue((self.workspace / rel).is_dir(), rel)
        for rel in ("knowledge", "projects", "research"):
            self.assertFalse((self.workspace / rel).exists(), rel)
        self.assertFalse((self.workspace / "_views").exists())

        index = self.workspace / "index.md"
        self.assertTrue(index.is_file())
        index_text = index.read_text(encoding="utf-8")
        self.assertIn("Slash commands are optional shortcuts", index_text)
        self.assertIn("Process everything in my inbox", index_text)
        self.assertIn("inbox/pending/", index_text)

        install = read_note(vault=str(self.workspace), file="_system/install.yaml")
        self.assertEqual(install["status"], "ok")
        self.assertIn("workspace_type: headless", install["body"])
        self.assertIn(str(self.workspace), install["body"])

        config = read_note(vault=str(self.workspace), file="_system/config.md")
        self.assertEqual(config["status"], "ok")
        self.assertEqual(config["frontmatter"]["tars-user-name"], "Ajay")
        self.assertEqual(config["frontmatter"]["tars-user-title"], "Product Leader")

        created = create_note(
            vault=str(self.workspace),
            path="memory/people/sarah.md",
            frontmatter={"tags": ["tars/person"], "tars-name": "Sarah"},
            body="# Sarah\n\nOwns onboarding.",
        )
        self.assertEqual(created["status"], "ok", created)
        found = search_by_tag(vault=str(self.workspace), tag="tars/person", query="onboarding")
        self.assertEqual(found["status"], "ok")
        self.assertEqual(found["count"], 1)
        self.assertEqual(found["results"][0]["path"], "memory/people/sarah.md")

    def test_obsidian_mode_uses_same_workspace_with_views(self) -> None:
        result = scaffold_workspace(
            vault=str(self.workspace),
            workspace_type="obsidian",
            user_name="Taylor",
            user_role="Engineering Manager",
            company="Acme",
            persona="engineering-manager",
        )
        self.assertEqual(result["status"], "ok", result)
        install = (self.workspace / "_system" / "install.yaml").read_text(encoding="utf-8")
        self.assertIn("workspace_type: obsidian", install)
        self.assertIn("obsidian_enabled: true", install)
        self.assertIn(f'obsidian_vault_path: "{self.workspace.resolve()}"', install)
        self.assertTrue((self.workspace / "memory").is_dir())
        self.assertTrue((self.workspace / "inbox" / "pending").is_dir())
        self.assertTrue((self.workspace / "index.md").is_file())
        self.assertTrue((self.workspace / "_views").is_dir())
        self.assertTrue((self.workspace / "_views" / "inbox-pending.base").is_file())
        for rel in ("knowledge", "projects", "research"):
            self.assertFalse((self.workspace / rel).exists(), rel)

    def test_end_to_end_framework_plumbing(self) -> None:
        scaffold = scaffold_workspace(
            vault=str(self.workspace),
            workspace_type="headless",
            user_name="Jordan",
            user_role="Sales",
            company="Northwind",
            persona="sales-customer-facing",
        )
        self.assertEqual(scaffold["status"], "ok", scaffold)

        person = create_note(
            vault=str(self.workspace),
            path="memory/people/alex.md",
            frontmatter={
                "tags": ["tars/person"],
                "tars-name": "Alex",
                "tars-status": "active",
            },
            body="# Alex\n\nAlex owns renewal risk for Northwind.",
        )
        self.assertEqual(person["status"], "ok", person)

        task = create_note(
            vault=str(self.workspace),
            path="tasks/2026-05-06-follow-up.md",
            frontmatter={
                "tags": ["tars/task"],
                "tars-status": "open",
                "tars-owner": "Jordan",
                "tars-due": "2026-05-08",
            },
            body="# Follow up\n\nSend renewal recap to [[memory/people/alex]].",
        )
        self.assertEqual(task["status"], "ok", task)

        appended = append_note(
            vault=str(self.workspace),
            file="memory/people/alex.md",
            content="\n\n## Update\n\nMentioned procurement timeline.",
        )
        self.assertEqual(appended["status"], "ok", appended)

        updated = update_frontmatter(
            vault=str(self.workspace),
            file="memory/people/alex.md",
            updates={"tars-relationship": "customer"},
        )
        self.assertEqual(updated["status"], "ok", updated)

        people = search_by_tag(
            vault=str(self.workspace),
            tag="tars/person",
            query="procurement",
            frontmatter={"tars-relationship": "customer"},
        )
        self.assertEqual(people["status"], "ok")
        self.assertEqual(people["count"], 1)

        blocked_archive = archive_note(vault=str(self.workspace), file="memory/people/alex.md")
        self.assertEqual(blocked_archive["status"], "error")
        self.assertIn("archive guardrail blocked", blocked_archive["reason"])

        moved = move_note(
            vault=str(self.workspace),
            src="memory/people/alex.md",
            dst="memory/people/alex-renewal.md",
        )
        self.assertEqual(moved["status"], "ok", moved)
        task_text = (self.workspace / "tasks" / "2026-05-06-follow-up.md").read_text()
        self.assertIn("[[memory/people/alex-renewal]]", task_text)

        report = create_note(
            vault=str(self.workspace),
            path="inbox/pending/northwind-renewal-report.md",
            frontmatter={"tags": ["tars/inbox"], "tars-source-type": "report"},
            body="# Renewal report\n\nBudget approved. Decision maker wants timeline by Friday.",
        )
        self.assertEqual(report["status"], "ok", report)
        classified = classify_file(vault=str(self.workspace), path="inbox/pending/northwind-renewal-report.md")
        self.assertEqual(classified["status"], "ok")
        self.assertTrue(classified["proposed"].startswith("contexts/"))

        artifact_body = "# Duplicate artifact\n\nSame body for duplicate detection."
        for name in ("dup-a.md", "dup-b.md"):
            r = create_note(
                vault=str(self.workspace),
                path=f"contexts/artifacts/{name}",
                frontmatter={"tags": ["tars/companion"]},
                body=artifact_body,
            )
            self.assertEqual(r["status"], "ok", r)
        duplicates = detect_near_duplicates(vault=str(self.workspace), folder="contexts/artifacts")
        self.assertEqual(duplicates["status"], "ok")
        self.assertGreaterEqual(duplicates["cluster_count"], 1)

        (self.workspace / "_system" / "guardrails.yaml").write_text(
            "block_patterns:\n"
            "  - name: api_key\n"
            "    pattern: sk-[A-Za-z0-9]{8,}\n"
            "warn_patterns:\n"
            "  - name: compensation\n"
            "    pattern: compensation\n",
            encoding="utf-8",
        )
        secret_scan = scan_secrets(vault=str(self.workspace), content="token sk-1234567890 and compensation note")
        self.assertEqual(secret_scan["status"], "ok")
        self.assertEqual(secret_scan["classification"], "block")
        self.assertEqual(secret_scan["total"], 2)

        build_script = REPO / "scripts" / "build-search-index.py"
        import subprocess

        build = subprocess.run(
            [sys.executable, str(build_script), "--vault", str(self.workspace), "--apply", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(build.returncode, 0, build.stderr + build.stdout)

        fts = fts_search(vault=str(self.workspace), query="renewal", scope="memory")
        self.assertEqual(fts["status"], "ok", fts)
        self.assertGreaterEqual(fts["count"], 1)

        semantic = semantic_search(vault=str(self.workspace), query="budget timeline", scope="all")
        self.assertIn(semantic["status"], {"ok", "fts_only", "no_index"}, semantic)
        if semantic["status"] != "no_index":
            self.assertIn("results", semantic)


if __name__ == "__main__":
    unittest.main(verbosity=2)

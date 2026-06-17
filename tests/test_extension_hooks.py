#!/usr/bin/env python3
"""Hook smoke tests for extension provider-bypass enforcement."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExtensionHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="tars-hook-test-")
        self.vault = Path(self.tmp)
        (self.vault / "_system").mkdir(parents=True)
        ext_dir = self.vault / "extensions" / "meeting-recording.zoom"
        ext_dir.mkdir(parents=True)
        (ext_dir / "extension.yaml").write_text(
            "id: meeting-recording.zoom\n"
            "name: Zoom Recording Adapter\n"
            "version: \"1.0.0\"\n"
            "tars_extension_version: \"1\"\n"
            "type: provider-adapter\n"
            "capabilities:\n"
            "  - meeting-recording\n"
            "applies_to:\n"
            "  skills:\n"
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
            "    - meeting-recording\n"
            "  provider_tools:\n"
            "    - mcp__zoom__.*\n"
            "  enforcement: required\n"
        )
        (ext_dir / "instructions.md").write_text("# Zoom Adapter\n")
        (ext_dir / "tool-contract.yaml").write_text("provider: zoom\n")
        (self.vault / "_system" / "extensions.yaml").write_text(
            "version: \"1\"\n"
            "extensions:\n"
            "  meeting-recording.zoom:\n"
            "    enabled: true\n"
            "    source: local\n"
            "    root: workspace\n"
            "    path: extensions/meeting-recording.zoom\n"
            "    installed_version: \"1.0.0\"\n"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_hook(self, script: str, event: dict) -> dict:
        env = dict(os.environ)
        env["TARS_VAULT_PATH"] = str(self.vault)
        proc = subprocess.run(
            ["python3", str(ROOT / "hooks" / script)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env=env,
            check=True,
        )
        return json.loads(proc.stdout or "{}")

    def test_provider_tool_blocked_until_extension_loaded(self) -> None:
        session_id = "session-1"
        self._run_hook("instructions-loaded.py", {"session_id": session_id, "skill": "maintain"})

        denied = self._run_hook(
            "pre-tool-use.py",
            {"session_id": session_id, "tool_name": "mcp__zoom__search_meetings", "tool_input": {}},
        )
        decision = denied["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")
        self.assertIn("meeting-recording.zoom", denied["hookSpecificOutput"]["permissionDecisionReason"])

        self._run_hook(
            "post-tool-use.py",
            {
                "session_id": session_id,
                "tool_name": "mcp__tars_vault__read_extension",
                "tool_input": {"extension_id": "meeting-recording.zoom"},
                "tool_response": {},
            },
        )

        allowed = self._run_hook(
            "pre-tool-use.py",
            {"session_id": session_id, "tool_name": "mcp__zoom__search_meetings", "tool_input": {}},
        )
        self.assertEqual(allowed, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)

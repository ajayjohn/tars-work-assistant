"""Adversarial MCP probes — Layer 3 of PRD-18.

Each probe asserts the dispatcher's documented contract:
- unknown kwargs rejected
- writes blocked on workspace mismatch
- vault resolver fails closed when no signal
- protected paths refuse direct ops
- schema validation rejects bad frontmatter
- scan_secrets covers expanded patterns

Usage:
    python3 -m tests.regression.run_adversarial_probes [--base /tmp/tars-qa]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "mcp" / "tars-vault" / "src"))

from tars_vault import server as srv  # noqa: E402


def call(name: str, args: dict) -> dict:
    return srv._call_handler_sync(name, args, "")


def _assert(cond: bool, msg: str, violations: list[str]) -> None:
    if not cond:
        violations.append(msg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/tmp/tars-qa")
    args = ap.parse_args()
    base = Path(args.base)

    # Make sure scenarios exist; if not, scaffold them.
    s2 = base / "s2-fresh-headless"
    s5 = base / "s5-path-mismatch"
    s1 = base / "s1-empty"
    if not s2.is_dir() or not s5.is_dir() or not s1.is_dir():
        import subprocess
        subprocess.run([sys.executable, "-m", "tests.regression.scaffold_scenarios",
                        "--base", str(base)], cwd=str(REPO_ROOT), check=True)

    # Drop a real existing note in s2 we can move/archive against
    (s2 / "memory" / "initiatives").mkdir(parents=True, exist_ok=True)
    real_note = s2 / "memory" / "initiatives" / "real.md"
    real_note.write_text(
        '---\n'
        'tars-summary: real\n'
        'tars-status: active\n'
        'tars-owner: "[[A]]"\n'
        'tars-created: "2026-05-08"\n'
        'tars-modified: "2026-05-08"\n'
        'tags: [tars/initiative]\n'
        '---\n# real\n',
        encoding="utf-8",
    )

    probes: list[dict] = []
    violations: list[str] = []

    # C1: unknown kwarg rejected
    r = call("write_note_from_content",
             {"vault": str(s2), "path": "memory/c1-garbage.md",
              "garbage": "x", "frontmatter": {"tars-summary": "x"}, "body": "b"})
    probes.append({"label": "C1 unknown kwarg", "result": r})
    _assert(r.get("status") == "error" and "unknown argument" in r.get("reason", ""),
            "C1 unknown-kwarg should fail with 'unknown argument'", violations)

    # C1: content blob path works
    r = call("write_note_from_content",
             {"vault": str(s2), "path": "memory/c1-blob.md",
              "content": "---\ntars-summary: blob\n---\nbody"})
    probes.append({"label": "C1 content blob writes non-empty", "result": r})
    _assert(r.get("status") == "ok" and r.get("bytes", 0) > 0,
            "C1 content blob should write non-empty file", violations)

    # C1: split fields still work
    r = call("write_note_from_content",
             {"vault": str(s2), "path": "memory/c1-split.md",
              "frontmatter": {"tars-summary": "split"},
              "body": "split body"})
    probes.append({"label": "C1 split frontmatter+body", "result": r})
    _assert(r.get("status") == "ok" and r.get("bytes", 0) > 0,
            "C1 split shape should write non-empty file", violations)

    # C1: mixed args rejected
    r = call("write_note_from_content",
             {"vault": str(s2), "path": "memory/c1-mixed.md",
              "content": "---\ntars-summary: a\n---\nb",
              "frontmatter": {"tars-summary": "x"}})
    probes.append({"label": "C1 mixed shapes rejected", "result": r})
    _assert(r.get("status") == "error",
            "C1 mixed shape should error", violations)

    # C2: writes blocked on path mismatch
    r = call("create_note",
             {"vault": str(s5), "path": "memory/should-block.md",
              "frontmatter": {"tags": ["tars/initiative"], "tars-summary": "x",
                              "tars-status": "active", "tars-owner": "[[A]]",
                              "tars-created": "2026-05-08", "tars-modified": "2026-05-08"},
              "body": "b"})
    probes.append({"label": "C2 mismatch blocks write", "result": r})
    _assert(r.get("status") == "error" and "match" in r.get("reason", "").lower(),
            "C2 path-mismatch should block writes", violations)

    # C2: reads pass through on mismatch
    r = call("read_note", {"vault": str(s5), "file": "memory/anything"})
    probes.append({"label": "C2 mismatch read still attempted", "result": r})
    _assert(r.get("status") == "error" and "not found" in r.get("reason", ""),
            "C2 read on mismatch should reach the lookup (not block)", violations)

    # C3: vault resolver fail-closed
    saved_env = os.environ.pop("TARS_VAULT_PATH", None)
    saved_cwd = os.getcwd()
    os.chdir(str(s1))
    try:
        r = call("read_note", {"file": "x"})
    finally:
        os.chdir(saved_cwd)
        if saved_env is not None:
            os.environ["TARS_VAULT_PATH"] = saved_env
    probes.append({"label": "C3 vault resolver fails closed", "result": r})
    _assert(r.get("status") == "error" and (
        "does not know which workspace" in r.get("reason", "") or
        "TARS_VAULT_PATH" in r.get("reason", "")
    ), "C3 unresolved vault should produce a clean error", violations)

    # C4: schema-validation rejects missing required props for tars/person
    r = call("create_note",
             {"vault": str(s2), "path": "memory/people/missing.md",
              "frontmatter": {"tags": ["tars/person"], "tars-summary": "x"},
              "body": "b"})
    probes.append({"label": "C4 missing required tars-staleness", "result": r})
    _assert(r.get("status") == "error" and "tars-staleness" in r.get("reason", ""),
            "C4 missing required property should be rejected", violations)

    # C4: enum violation
    r = call("create_note",
             {"vault": str(s2), "path": "memory/initiatives/badenum.md",
              "frontmatter": {"tags": ["tars/initiative"], "tars-summary": "x",
                              "tars-status": "BOGUS", "tars-owner": "[[A]]",
                              "tars-created": "2026-05-08", "tars-modified": "2026-05-08"},
              "body": "b"})
    probes.append({"label": "C4 enum violation", "result": r})
    _assert(r.get("status") == "error" and "BOGUS" in r.get("reason", ""),
            "C4 enum violation should be rejected", violations)

    # C4: validate=false escape hatch
    r = call("create_note",
             {"vault": str(s2), "path": "memory/people/stub.md",
              "frontmatter": {"tags": ["tars/person"], "tars-summary": "x"},
              "body": "b", "validate": False})
    probes.append({"label": "C4 validate=false bypass", "result": r})
    _assert(r.get("status") == "ok",
            "C4 validate=false should bypass schema check", violations)

    # M3: archive a protected file
    r = call("archive_note", {"vault": str(s2), "file": "_system/install.yaml",
                              "dry_run": True})
    probes.append({"label": "M3 archive _system/install.yaml blocked", "result": r})
    _assert(r.get("status") == "error" and "protected" in r.get("reason", "").lower()
            or "managed by TARS" in r.get("reason", ""),
            "M3 archive_note must reject _system/", violations)

    # M3: move into _system blocked
    r = call("move_note", {"vault": str(s2),
                           "src": "memory/initiatives/real.md",
                           "dst": "_system/sneaky.md"})
    probes.append({"label": "M3 move into _system blocked", "result": r})
    _assert(r.get("status") == "error" and (
        "protected" in r.get("reason", "").lower() or
        "managed by TARS" in r.get("reason", "")
    ), "M3 move_note dst into _system must be rejected", violations)

    # M3 escape hatch — schema-allowed allow_protected_paths kwarg
    r = call("update_frontmatter", {
        "vault": str(s2), "file": "_system/install.yaml",
        "updates": {"tars-test-escape": "ok"},
        "allow_protected_paths": True,
    })
    probes.append({"label": "M3 escape hatch (allow_protected_paths)", "result": r})
    _assert(r.get("status") == "ok",
            "M3 escape hatch should permit /welcome-style writes", violations)
    # cleanup the test stamp
    call("update_frontmatter", {
        "vault": str(s2), "file": "_system/install.yaml",
        "updates": {"tars-test-escape": None},
        "allow_protected_paths": True,
    })

    # M2: read_system_file happy path
    r = call("read_system_file", {"vault": str(s2),
                                  "file": "_system/install.yaml"})
    probes.append({"label": "M2 read_system_file install.yaml", "result": r})
    _assert(r.get("status") == "ok" and (
        "data" in r or "parsed" in r or "frontmatter" in r
    ), "M2 should return parsed system file", violations)

    # M2: path traversal blocked
    r = call("read_system_file", {"vault": str(s2),
                                  "file": "_system/../../../etc/passwd"})
    probes.append({"label": "M2 path traversal blocked", "result": r})
    _assert(r.get("status") == "error",
            "M2 path traversal must be blocked", violations)

    # M2: outside _system blocked
    r = call("read_system_file", {"vault": str(s2), "file": "memory/x.md"})
    probes.append({"label": "M2 outside _system blocked", "result": r})
    _assert(r.get("status") == "error",
            "M2 outside-_system must be blocked", violations)

    # M4: secret-pattern coverage
    blob = ("AKIAIOSFODNN7EXAMPLE xoxb-1234567890-abcdef "
            "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa "
            "sk_live_aaaaaaaaaaaaaaaaaaaaaaaa")
    r = call("scan_secrets", {"vault": str(s2), "content": blob})
    probes.append({"label": "M4 secret patterns", "result": r})
    names = {h.get("name") for h in r.get("hits", [])}
    must_match = {"aws_key", "slack_bot_token", "github_pat", "stripe_secret"}
    missing = sorted(must_match - names)
    _assert(not missing,
            f"M4 missing patterns: {missing}", violations)

    # update_frontmatter both call shapes
    r = call("update_frontmatter", {"vault": str(s2),
                                    "file": "memory/initiatives/real.md",
                                    "property": "tars-modified", "value": "2026-05-09"})
    probes.append({"label": "update_frontmatter legacy (property/value)", "result": r})
    _assert(r.get("status") == "ok",
            "legacy property/value shape must still work", violations)

    r = call("update_frontmatter", {"vault": str(s2),
                                    "file": "memory/initiatives/real.md",
                                    "updates": {"tars-modified": "2026-05-10"}})
    probes.append({"label": "update_frontmatter canonical (updates)", "result": r})
    _assert(r.get("status") == "ok",
            "canonical updates shape must work", violations)

    # cleanup test fixtures created above
    for f in ("memory/c1-blob.md", "memory/c1-split.md",
              "memory/people/stub.md", "memory/initiatives/real.md"):
        p = s2 / f
        if p.is_file():
            p.unlink()

    summary = {
        "layer": "adversarial",
        "probes_total": len(probes),
        "violations": violations,
        "passed": len(probes) - len(violations),
        "failed": len(violations),
        "probes": probes,
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate Phase 5 + Phase 6 deliverables (§5 backlog fixes + §8.10 /create).

Structural only — does not invoke MCP tools or rendering skills. Verifies the
files, frontmatter pointers, and schema additions the executing agent shipped
in Session 4 land correctly on disk. Stdlib-only.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def check_brand_auto_load(errors: list[str]) -> None:
    # templates/brand-guidelines.md exists with tars-brand: true
    brand = ROOT / "templates" / "brand-guidelines.md"
    if not brand.is_file():
        fail("MISSING: templates/brand-guidelines.md", errors)
        return
    text = brand.read_text(encoding="utf-8")
    if "tars-brand: true" not in text:
        fail("templates/brand-guidelines.md missing `tars-brand: true` frontmatter flag", errors)

    # /communicate Step 0 brand auto-load
    comm = (ROOT / "skills" / "communicate" / "SKILL.md").read_text(encoding="utf-8")
    if "Step 0: Brand auto-load" not in comm:
        fail("skills/communicate/SKILL.md missing Step 0 brand auto-load section", errors)
    if "tars-active-brand" not in comm:
        fail("skills/communicate/SKILL.md does not reference tars-active-brand cache", errors)

    # /create Step 2 brand auto-load + Step 7 pass brand pointer
    create = (ROOT / "skills" / "create" / "SKILL.md").read_text(encoding="utf-8")
    if "Step 2: Brand auto-load" not in create:
        fail("skills/create/SKILL.md missing Step 2 brand auto-load section", errors)
    if "Brand guidelines:" not in create:
        fail("skills/create/SKILL.md does not pass brand pointer in render-skill prompt", errors)


def check_framework_self_state(errors: list[str]) -> None:
    sync = (ROOT / "scripts" / "sync.py").read_text(encoding="utf-8")
    if "compute_hydration" not in sync:
        fail("scripts/sync.py missing compute_hydration()", errors)
    if "--hydration" not in sync:
        fail("scripts/sync.py missing --hydration flag", errors)
    if "decision_count" not in sync:
        fail("scripts/sync.py does not compute decision_count (the original drift bug)", errors)

    briefing = (ROOT / "skills" / "briefing" / "SKILL.md").read_text(encoding="utf-8")
    # The "Level 2 (15 people, 42 meetings)" artifact text must be gone.
    if "Level 2 (15 people, 42 meetings)" in briefing:
        fail("skills/briefing/SKILL.md still contains the hardcoded 'Level 2' artifact", errors)
    if "sync.py --hydration" not in briefing:
        fail("skills/briefing/SKILL.md does not reference sync.py --hydration for live counts", errors)


def check_task_lifecycle(errors: list[str]) -> None:
    schema = (ROOT / "_system" / "schemas.yaml").read_text(encoding="utf-8")
    for field in ("tars-blocked-by", "tars-age-days", "tars-escalation-level"):
        if field not in schema:
            fail(f"_system/schemas.yaml missing task optional field {field}", errors)
    if "tars-brand" not in schema:
        fail("_system/schemas.yaml missing context-artifact optional field tars-brand", errors)
    if "tars-draft-status" not in schema:
        fail("_system/schemas.yaml missing context-artifact optional field tars-draft-status", errors)

    tasks = (ROOT / "skills" / "tasks" / "SKILL.md").read_text(encoding="utf-8")
    if "Escalation level semantics" not in tasks:
        fail("skills/tasks/SKILL.md missing 'Escalation level semantics' section", errors)

    lint = (ROOT / "skills" / "lint" / "SKILL.md").read_text(encoding="utf-8")
    if "Task age + escalation" not in lint:
        fail("skills/lint/SKILL.md check table missing 'Task age + escalation' row", errors)


def check_telemetry_plumbing(errors: list[str]) -> None:
    common = (ROOT / "hooks" / "_common.py").read_text(encoding="utf-8")
    if "def append_telemetry" not in common:
        fail("hooks/_common.py missing append_telemetry helper", errors)

    post = (ROOT / "hooks" / "post-tool-use.py").read_text(encoding="utf-8")
    if "MUTATING_TOOLS" not in post:
        fail("hooks/post-tool-use.py missing MUTATING_TOOLS allowlist", errors)
    if "vault_write" not in post:
        fail("hooks/post-tool-use.py does not emit vault_write telemetry event", errors)

    loaded = (ROOT / "hooks" / "instructions-loaded.py").read_text(encoding="utf-8")
    if "skill_loaded" not in loaded:
        fail("hooks/instructions-loaded.py does not emit skill_loaded telemetry event", errors)

    base = (ROOT / "_views" / "skill-activity.base")
    if not base.is_file():
        fail("MISSING: _views/skill-activity.base", errors)


def check_office_templates(errors: list[str]) -> None:
    office = ROOT / "templates" / "office"
    if not office.is_dir():
        fail("MISSING: templates/office/ directory", errors)
        return
    expected = [
        "README.md",
        "deck-executive.md",
        "deck-narrative.md",
        "deck-technical-review.md",
        "spreadsheet-kpi-dashboard.md",
        "spreadsheet-roadmap.md",
        "doc-decision-memo.md",
        "doc-project-status.md",
        "html-board-update.md",
    ]
    for f in expected:
        if not (office / f).is_file():
            fail(f"MISSING: templates/office/{f}", errors)


def check_create_delegation(errors: list[str]) -> None:
    create = (ROOT / "skills" / "create" / "SKILL.md").read_text(encoding="utf-8")
    required_bits = [
        "Step 0: Capability probe",
        "Step 4: Format selection",
        "Step 5: Content-first draft",
        "Step 7: Delegate render",
        "Step 8: Verify + companion",
        "Step 9: Telemetry",
        "anthropic-skill:",
        "contexts/artifacts/",
    ]
    for token in required_bits:
        if token not in create:
            fail(f"skills/create/SKILL.md missing expected marker: {token!r}", errors)
    # Forbidden: any reintroduction of office MCP *as an instruction*.
    # The skill body is allowed — indeed encouraged — to name these libs in a
    # prohibition (e.g., "TARS does not bundle python-pptx, weasyprint, ..."),
    # so we only fail on patterns that suggest actual import/use.
    forbidden = ["mcp/tars-office", "import pptx", "from pptx", "import docx",
                 "from docx", "import openpyxl", "from openpyxl"]
    for token in forbidden:
        if token in create:
            fail(f"skills/create/SKILL.md contains forbidden office-MCP marker: {token!r}", errors)


def check_welcome_probe(errors: list[str]) -> None:
    welcome = (ROOT / "skills" / "welcome" / "SKILL.md").read_text(encoding="utf-8")
    if "tars-anthropic-skills" not in welcome:
        fail("skills/welcome/SKILL.md missing tars-anthropic-skills config key", errors)
    if "templates/brand-guidelines.md" not in welcome:
        fail("skills/welcome/SKILL.md does not reference the brand-guidelines template", errors)


def main() -> int:
    errors: list[str] = []
    check_brand_auto_load(errors)
    check_framework_self_state(errors)
    check_task_lifecycle(errors)
    check_telemetry_plumbing(errors)
    check_office_templates(errors)
    check_create_delegation(errors)
    check_welcome_probe(errors)

    if errors:
        print("Phase 5/6 validator — errors:")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\nResult: {len(errors)} errors")
        print("STATUS: FAIL")
        return 1
    print("  ✓ Phase 5 + Phase 6 deliverables present and wired correctly")
    print("\nResult: 0 errors")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

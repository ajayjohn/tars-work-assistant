#!/usr/bin/env python3
"""Validate that always-loaded harness files stay compact."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_BUDGET = 12_000
SKILL_CARD_BUDGET = 14_000
CLAUDE_BUDGET = 10_000
SPLIT_SKILLS = {"core", "briefing", "meeting", "maintain", "learn", "think", "ideate"}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    claude = ROOT / "CLAUDE.md"
    if claude.is_file() and claude.stat().st_size > CLAUDE_BUDGET:
        fail(f"CLAUDE.md exceeds budget: {claude.stat().st_size} > {CLAUDE_BUDGET}", errors)

    skills = ROOT / "skills"
    for skill_dir in sorted(p for p in skills.iterdir() if p.is_dir() and p.name in SPLIT_SKILLS):
        card = skill_dir / "SKILL.md"
        if not card.is_file():
            continue
        size = card.stat().st_size
        budget = CORE_BUDGET if skill_dir.name == "core" else SKILL_CARD_BUDGET
        if size > budget:
            fail(f"skills/{skill_dir.name}/SKILL.md exceeds budget: {size} > {budget}", errors)
        if skill_dir.name in SPLIT_SKILLS:
            refs = skill_dir / "references"
            if not refs.is_dir():
                fail(f"skills/{skill_dir.name}/ missing references/ after split", errors)
            elif not any(p.name != "legacy-full-protocol.md" and p.suffix == ".md" for p in refs.iterdir()):
                fail(f"skills/{skill_dir.name}/references/ lacks mode-specific reference files", errors)

    if errors:
        print("Harness budget validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Harness budget validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

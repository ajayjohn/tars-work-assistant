#!/usr/bin/env python3
"""
TARS v3 Smoke Tests
Quick verification that the framework is properly set up.
Run after scaffolding or at session start.

Usage: python3 tests/smoke-tests.py [vault_path]
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def check_obsidian_cli():
    """Verify obsidian-cli is available."""
    try:
        result = subprocess.run(
            ["obsidian", "version"],
            capture_output=True, text=True, timeout=10,
        )
        return {
            "test": "obsidian-cli available",
            "pass": result.returncode == 0,
            "detail": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
        }
    except FileNotFoundError:
        return {
            "test": "obsidian-cli available",
            "pass": False,
            "detail": "obsidian command not found in PATH",
        }
    except subprocess.TimeoutExpired:
        return {
            "test": "obsidian-cli available",
            "pass": False,
            "detail": "obsidian command timed out",
        }


def check_vault_accessible():
    """Verify vault is accessible via obsidian-cli."""
    try:
        result = subprocess.run(
            ["obsidian", "vault"],
            capture_output=True, text=True, timeout=10,
        )
        return {
            "test": "vault accessible",
            "pass": result.returncode == 0 and "path" in result.stdout.lower(),
            "detail": result.stdout.strip()[:200],
        }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {
            "test": "vault accessible",
            "pass": False,
            "detail": "Could not query vault info",
        }


def check_required_dirs(vault_path):
    """Verify all required directories exist."""
    vault = Path(vault_path)
    required = [
        "_system", "_system/changelog", "_system/backlog", "_system/backlog/issues",
        "_system/backlog/ideas", "_views", "memory", "memory/people", "memory/vendors",
        "memory/competitors", "memory/products", "memory/initiatives", "memory/decisions",
        "memory/org-context", "journal", "contexts", "inbox", "inbox/pending",
        "inbox/processed", "archive", "archive/transcripts", "templates", "scripts",
        "skills", "tests",
    ]

    missing = [d for d in required if not (vault / d).exists()]

    return {
        "test": "required directories",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} directories present",
    }


def check_system_files(vault_path):
    """Verify all _system/ files exist."""
    vault = Path(vault_path)
    required = [
        "_system/config.md",
        "_system/integrations.md",
        "_system/alias-registry.md",
        "_system/taxonomy.md",
        "_system/kpis.md",
        "_system/schedule.md",
        "_system/guardrails.yaml",
        "_system/maturity.yaml",
        "_system/housekeeping-state.yaml",
        "_system/schemas.yaml",
    ]

    missing = [f for f in required if not (vault / f).exists()]

    return {
        "test": "system files",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} system files present",
    }


def check_schemas(vault_path):
    """Verify schemas.yaml exists and parses."""
    schema_path = Path(vault_path) / "_system" / "schemas.yaml"
    if not schema_path.exists():
        return {
            "test": "schemas.yaml valid",
            "pass": False,
            "detail": "File not found",
        }

    try:
        with open(schema_path) as f:
            if HAS_YAML:
                data = yaml.safe_load(f)
            else:
                data = {"_note": "YAML parsing skipped — PyYAML not available"}
                return {
                    "test": "schemas.yaml valid",
                    "pass": True,
                    "detail": "File exists (YAML parse skipped — no PyYAML)",
                }

        if not isinstance(data, dict):
            return {"test": "schemas.yaml valid", "pass": False, "detail": "Not a valid YAML dict"}

        expected_types = ["person", "initiative", "decision", "meeting", "task",
                          "briefing", "wisdom", "vendor", "competitor", "product",
                          "transcript", "companion", "issue", "idea"]
        present = [t for t in expected_types if t in data]
        missing = [t for t in expected_types if t not in data]

        return {
            "test": "schemas.yaml valid",
            "pass": len(missing) == 0,
            "detail": f"{len(present)} types defined" + (f", missing: {missing}" if missing else ""),
        }
    except Exception as e:
        return {"test": "schemas.yaml valid", "pass": False, "detail": str(e)}


def check_alias_registry(vault_path):
    """Verify alias registry exists and parses."""
    path = Path(vault_path) / "_system" / "alias-registry.md"
    if not path.exists():
        return {"test": "alias-registry exists", "pass": False, "detail": "File not found"}

    try:
        with open(path) as f:
            content = f.read()
        has_tables = "Short Name" in content or "Abbreviation" in content
        return {
            "test": "alias-registry exists",
            "pass": True,
            "detail": f"Present, {len(content)} chars" + (" (has tables)" if has_tables else ""),
        }
    except Exception as e:
        return {"test": "alias-registry exists", "pass": False, "detail": str(e)}


def check_templates(vault_path):
    """Verify all templates exist."""
    vault = Path(vault_path)
    required = [
        "person", "vendor", "competitor", "product", "initiative", "decision",
        "org-context", "meeting-journal", "briefing",
        "wisdom-journal", "companion", "transcript", "backlog-item",
    ]

    missing = [t for t in required if not (vault / "templates" / f"{t}.md").exists()]

    return {
        "test": "templates",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} templates present",
    }


def check_base_views(vault_path):
    """Verify all .base view files exist."""
    vault = Path(vault_path)
    required = [
        "all-people", "all-initiatives", "all-decisions", "all-products",
        "all-vendors", "all-competitors", "recent-journal", "active-tasks",
        "overdue-tasks", "stale-memory", "inbox-pending", "all-documents",
        "all-transcripts", "flagged-content", "backlog",
    ]

    missing = [b for b in required if not (vault / "_views" / f"{b}.base").exists()]

    return {
        "test": "base views",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} base views present",
    }


def check_scripts(vault_path):
    """Verify all required scripts exist."""
    vault = Path(vault_path)
    required = [
        "validate-schema.py", "scan-secrets.py", "health-check.py",
    ]

    missing = [s for s in required if not (vault / "scripts" / s).exists()]

    return {
        "test": "scripts",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} scripts present",
    }


def check_skills(vault_path):
    """Verify all skill definitions exist."""
    vault = Path(vault_path)
    required = [
        "core/SKILL.md", "welcome/SKILL.md", "learn/SKILL.md", "tasks/SKILL.md",
        "meeting/SKILL.md", "briefing/SKILL.md", "answer/SKILL.md",
        "maintain/SKILL.md",
    ]

    missing = [s for s in required if not (vault / "skills" / s).exists()]

    return {
        "test": "skills (Phase 1)",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} Phase 1 skills present",
    }


def check_obsidian_skills(vault_path):
    """Verify obsidian-skills are installed."""
    vault = Path(vault_path)
    required = [
        "obsidian-cli/SKILL.md",
        "obsidian-bases/SKILL.md",
        "obsidian-markdown/SKILL.md",
        "json-canvas/SKILL.md",
        "defuddle/SKILL.md",
    ]

    missing = [s for s in required if not (vault / ".claude" / "skills" / s).exists()]

    return {
        "test": "obsidian-skills installed",
        "pass": len(missing) == 0,
        "detail": f"Missing: {', '.join(missing)}" if missing else f"All {len(required)} obsidian skills present",
    }


def check_daily_note():
    """Verify daily note is accessible."""
    try:
        result = subprocess.run(
            ["obsidian", "daily:path"],
            capture_output=True, text=True, timeout=10,
        )
        return {
            "test": "daily note accessible",
            "pass": result.returncode == 0,
            "detail": result.stdout.strip() if result.returncode == 0 else "daily note not configured or inaccessible",
        }
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {
            "test": "daily note accessible",
            "pass": False,
            "detail": "Could not check daily note",
        }


def check_schema_validation(vault_path):
    """Run schema validation script."""
    script = Path(vault_path) / "scripts" / "validate-schema.py"
    if not script.exists():
        return {"test": "schema validation", "pass": False, "detail": "Script not found"}

    try:
        result = subprocess.run(
            [sys.executable, str(script), vault_path],
            capture_output=True, text=True, timeout=30,
        )
        try:
            data = json.loads(result.stdout)
            summary = data.get("summary", {})
            return {
                "test": "schema validation",
                "pass": summary.get("invalid", 0) == 0,
                "detail": f"Scanned {summary.get('total_notes_scanned', 0)} notes, "
                          f"{summary.get('valid', 0)} valid, {summary.get('invalid', 0)} invalid",
            }
        except json.JSONDecodeError:
            return {
                "test": "schema validation",
                "pass": result.returncode == 0,
                "detail": result.stdout[:200] if result.stdout else result.stderr[:200],
            }
    except Exception as e:
        return {"test": "schema validation", "pass": False, "detail": str(e)}


def main():
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."

    tests = [
        check_obsidian_cli(),
        check_vault_accessible(),
        check_required_dirs(vault_path),
        check_system_files(vault_path),
        check_schemas(vault_path),
        check_alias_registry(vault_path),
        check_templates(vault_path),
        check_base_views(vault_path),
        check_scripts(vault_path),
        check_skills(vault_path),
        check_obsidian_skills(vault_path),
        check_daily_note(),
        check_schema_validation(vault_path),
    ]

    passed = sum(1 for t in tests if t["pass"])
    failed = len(tests) - passed

    output = {
        "timestamp": datetime.now().isoformat(),
        "vault_path": vault_path,
        "summary": {
            "total": len(tests),
            "passed": passed,
            "failed": failed,
        },
        "tests": tests,
    }

    print(json.dumps(output, indent=2))
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()

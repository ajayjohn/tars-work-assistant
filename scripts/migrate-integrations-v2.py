#!/usr/bin/env python3
"""migrate-integrations-v2 — upgrade a vault's ``_system/integrations.md`` from
the v3.0 narrative layout to the v3.1 capability-preference map.

Idempotent: running twice on the same vault is a no-op after the first pass.
Backs up the existing file to ``integrations.md.pre-v3.1-backup`` on first run.

Contract per PRD §26.15:
  --vault <path>   required
  --dry-run        print proposed new file, no writes
  --apply          write the upgrade (backs up original first)
  --json           emit machine-readable status
Exit codes: 0 OK, 1 interrupted, 2 error, 3 invalid state.

Phase 1b scope. The v3.1 template shipped by this script comes from
``templates/integrations-v2.md`` (see PRD §3.5).
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "templates" / "integrations-v2.md"
MARKER = "tars-config-version: \"2.0\""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="migrate-integrations-v2")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def target_path(vault: Path) -> Path:
    return vault / "_system" / "integrations.md"


def already_migrated(content: str) -> bool:
    return MARKER in content


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault path not a directory: {vault}", file=sys.stderr)
        return 3
    if not TEMPLATE_PATH.exists():
        print(f"error: template missing at {TEMPLATE_PATH}", file=sys.stderr)
        return 2

    target = target_path(vault)
    new_body = TEMPLATE_PATH.read_text(encoding="utf-8")
    existing = target.read_text(encoding="utf-8") if target.exists() else ""

    payload = {
        "status": "noop" if already_migrated(existing) else "pending",
        "vault": str(vault),
        "target": str(target),
        "template": str(TEMPLATE_PATH),
    }

    if already_migrated(existing):
        payload["note"] = "integrations.md already at v2.0 — no action taken."
    elif args.dry_run or not args.apply:
        payload["note"] = "Dry run — pass --apply to write. Original will be backed up to integrations.md.pre-v3.1-backup."
    else:
        backup = target.with_suffix(target.suffix + ".pre-v3.1-backup")
        if target.exists() and not backup.exists():
            shutil.copy2(target, backup)
            payload["backup"] = str(backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_body, encoding="utf-8")
        payload["status"] = "migrated"
        payload["note"] = "Wrote v3.1 integrations.md. Review and tune preferred providers."

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)

"""Scaffold the nine PRD-18 user scenarios under a base directory.

Each scenario simulates a distinct user state. Used by the regression suite
and also runnable standalone for manual probing.

All fixture dates are computed relative to "today" so the suite is
deterministic regardless of when CI runs:

  * `last_session_at` — for fresh / current scenarios, "today at 10:00 UTC";
    for the sparse scenario, "today minus 60 days".
  * `tars-created` / `tars-modified` — recent scenarios use yesterday;
    "stale" fixtures use today minus 60 days so the >30-day staleness check
    fires.

Usage:
    python3 -m tests.regression.scaffold_scenarios --base /tmp/tars-qa
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_SEED = REPO_ROOT / "_system"

SCENARIOS = [
    "s1-empty",
    "s2-fresh-headless",
    "s3-fresh-obsidian",
    "s4-stale-version",
    "s5-path-mismatch",
    "s6-polluted-frontmatter",
    "s7-mid-mode-switch",
    "s8-sparse-returning",
    "s9-advanced",
]

INSTALL_TEMPLATE = """workspace_type: {workspace_type}
workspace_path: "{path}"
vault_path: "{path}"
obsidian_enabled: {obsidian_enabled}
obsidian_vault_path: "{obsidian_vault_path}"
installation_id: "qa-{slug}"
persona: "product-leader"
plugin_version: "{plugin_version}"
created: "{created}"
last_session_at: "{last_session_at}"
"""


def _live_plugin_version() -> str:
    return json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json")
                       .read_text(encoding="utf-8"))["version"]


def _copy_seed(target_root: Path) -> None:
    sysdir = target_root / "_system"
    sysdir.mkdir(parents=True, exist_ok=True)
    for f in (
        "schemas.yaml", "housekeeping-state.yaml", "guardrails.yaml",
        "maturity.yaml", "activity-ledger.yaml",
    ):
        src = SYSTEM_SEED / f
        if src.is_file():
            shutil.copy2(src, sysdir / f)
    for f in (
        "kpis.md", "taxonomy.md", "alias-registry.md",
        "integrations.md", "config.md", "schedule.md",
    ):
        src = SYSTEM_SEED / f
        if src.is_file():
            shutil.copy2(src, sysdir / f)
    for sub in ("telemetry", "changelog"):
        (sysdir / sub).mkdir(exist_ok=True)
    for sub in ("memory", "inbox", "journal", "archive", "contexts", "tasks"):
        (target_root / sub).mkdir(exist_ok=True)


def _stamp_housekeeping_version(vault: Path, version: str) -> None:
    p = vault / "_system" / "housekeeping-state.yaml"
    if not p.is_file():
        return
    text = p.read_text(encoding="utf-8")
    new = []
    replaced = False
    for line in text.splitlines():
        if line.startswith("plugin_version:"):
            new.append(f'plugin_version: "{version}"')
            replaced = True
        else:
            new.append(line)
    if not replaced:
        new.append(f'plugin_version: "{version}"')
    p.write_text("\n".join(new) + "\n", encoding="utf-8")


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _set_mtime(path: Path, dt: datetime) -> None:
    ts = dt.timestamp()
    os.utime(path, (ts, ts))


def scaffold(base: Path) -> dict:
    base.mkdir(parents=True, exist_ok=True)
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    live = _live_plugin_version()
    paths: dict[str, Path] = {}

    # Compute every fixture date relative to "today" so the suite is
    # deterministic regardless of when CI runs.
    today_dt = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
    today = today_dt.date()
    today_iso = _iso(today_dt)
    yesterday = today - timedelta(days=1)
    sixty_days_ago_dt = today_dt - timedelta(days=60)
    sixty_days_ago_iso = _iso(sixty_days_ago_dt)
    sixty_days_ago_d = (today - timedelta(days=60)).isoformat()
    fortnight_ago_iso = _iso(today_dt - timedelta(days=23))
    forty_days_ago_iso = _iso(today_dt - timedelta(days=40))
    forty_days_ago_d = (today - timedelta(days=40)).isoformat()
    next_month = (today + timedelta(days=30)).strftime("%Y-%m")
    following_month = (today + timedelta(days=60)).strftime("%Y-%m")

    # s1-empty: just an empty directory
    p = base / "s1-empty"
    p.mkdir()
    paths["s1-empty"] = p

    # s2-fresh-headless
    p = base / "s2-fresh-headless"
    _copy_seed(p)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=p,
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s2",
        plugin_version=live,
        created=today_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s2-fresh-headless"] = p

    # s3-fresh-obsidian
    p = base / "s3-fresh-obsidian"
    _copy_seed(p)
    (p / "_views").mkdir()
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="obsidian",
        path=p,
        obsidian_enabled="true",
        obsidian_vault_path=p,
        slug="s3",
        plugin_version=live,
        created=today_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s3-fresh-obsidian"] = p

    # s4-stale-version
    p = base / "s4-stale-version"
    _copy_seed(p)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=p,
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s4",
        plugin_version="3.2.0",
        created=forty_days_ago_iso,
        last_session_at=fortnight_ago_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s4-stale-version"] = p

    # s5-path-mismatch
    p = base / "s5-path-mismatch"
    _copy_seed(p)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=base / "SOMEWHERE-ELSE",
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s5",
        plugin_version=live,
        created=today_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s5-path-mismatch"] = p

    # s6-polluted-frontmatter
    p = base / "s6-polluted-frontmatter"
    _copy_seed(p)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=p,
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s6",
        plugin_version=live,
        created=today_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    (p / "memory" / "initiatives").mkdir(parents=True)
    (p / "memory" / "initiatives" / "canonical-init.md").write_text(
        '---\n'
        'tars-summary: A canonical initiative\n'
        'tars-status: active\n'
        'tars-owner: "[[Alison Slowes]]"\n'
        f'tars-created: "{yesterday.isoformat()}"\n'
        f'tars-modified: "{yesterday.isoformat()}"\n'
        'tags: [tars/initiative]\n'
        'aliases: []\n'
        '---\n# Canonical Initiative\n', encoding="utf-8")
    (p / "memory" / "initiatives" / "polluted-init.md").write_text(
        '---\n'
        'title: Polluted Initiative\n'
        'pm: Alison Slowes\n'
        'status: active\n'
        f'start: {next_month}\n'
        f'end: {following_month}\n'
        'tags: [initiative, ai]\n'
        '---\n# Polluted Initiative\n', encoding="utf-8")
    paths["s6-polluted-frontmatter"] = p

    # s7-mid-mode-switch (orphaned _views from disable-obsidian)
    p = base / "s7-mid-mode-switch"
    _copy_seed(p)
    (p / "_views").mkdir()
    (p / "_views" / "initiatives.base").write_text(
        '# generated-by: tars 3.4.0\n'
        'filters: { and: [ { property: tags, contains: tars/initiative } ] }\n',
        encoding="utf-8")
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=p,
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s7",
        plugin_version=live,
        created=today_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s7-mid-mode-switch"] = p

    # s8-sparse-returning (60-day absence)
    p = base / "s8-sparse-returning"
    _copy_seed(p)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="headless",
        path=p,
        obsidian_enabled="false",
        obsidian_vault_path="",
        slug="s8",
        plugin_version=live,
        created=sixty_days_ago_iso,
        last_session_at=sixty_days_ago_iso,
    ))
    _stamp_housekeeping_version(p, live)
    paths["s8-sparse-returning"] = p

    # s9-advanced
    p = base / "s9-advanced"
    _copy_seed(p)
    (p / "_views").mkdir()
    (p / "memory" / "initiatives").mkdir(parents=True)
    (p / "memory" / "people").mkdir()
    (p / "memory" / "decisions").mkdir()
    (p / "inbox" / "pending").mkdir(parents=True)
    (p / "_system" / "install.yaml").write_text(INSTALL_TEMPLATE.format(
        workspace_type="obsidian",
        path=p,
        obsidian_enabled="true",
        obsidian_vault_path=p,
        slug="s9",
        plugin_version=live,
        created=forty_days_ago_iso,
        last_session_at=today_iso,
    ))
    _stamp_housekeeping_version(p, live)
    for i in range(1, 51):
        st = "completed" if i % 7 == 0 else "active"
        modified = sixty_days_ago_d if i % 10 == 0 else yesterday.isoformat()
        init_path = p / "memory" / "initiatives" / f"init-{i}.md"
        init_path.write_text(
            f'---\n'
            f'tars-summary: Initiative {i}\n'
            f'tars-status: {st}\n'
            f'tars-owner: "[[Person {i % 7}]]"\n'
            f'tars-created: "{forty_days_ago_d}"\n'
            f'tars-modified: "{modified}"\n'
            f'tags: [tars/initiative]\n'
            f'aliases: []\n'
            f'---\n# Initiative {i}\n', encoding="utf-8")
        _set_mtime(init_path, sixty_days_ago_dt if i % 10 == 0 else today_dt)
    for i, name in enumerate(("note", "transcript", "doc"), start=1):
        (p / "inbox" / "pending" / f"item-{i}.txt").write_text(name, encoding="utf-8")
    paths["s9-advanced"] = p

    return {k: str(v) for k, v in paths.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="/tmp/tars-qa")
    args = ap.parse_args()
    paths = scaffold(Path(args.base))
    print(json.dumps(paths, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

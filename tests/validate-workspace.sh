#!/usr/bin/env bash
# Fast validation for the local Markdown workspace TARS implementation.

set -u

FAIL=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; FAIL=1; }

[ -f commands/start.md ] && pass "/start command exists" || fail "/start command missing"
[ -f skills/start/SKILL.md ] && pass "/start skill exists" || fail "/start skill missing"
grep -q "preview-only" skills/start/SKILL.md && pass "/start preview-only stated" || fail "/start preview-only missing"
grep -qi "Do not write" skills/start/SKILL.md && pass "/start forbids default writes" || fail "/start write guard missing"

[ -f commands/help.md ] && pass "/help command exists" || fail "/help command missing"
[ -f commands/doctor.md ] && pass "/doctor command exists" || fail "/doctor command missing"
[ -f skills/doctor/SKILL.md ] && pass "/doctor skill exists" || fail "/doctor skill missing"
grep -q "Command groups" skills/core/SKILL.md && pass "core help grouped" || fail "core help groups missing"
grep -q "skills/start/" skills/core/SKILL.md && pass "/start routed" || fail "/start route missing"
grep -q "skills/doctor/" skills/core/SKILL.md && pass "/doctor routed" || fail "/doctor route missing"
grep -q -- "--continue-setup" skills/welcome/SKILL.md && pass "welcome continue setup documented" || fail "welcome continue setup missing"
grep -q "Natural-language example" mcp/tars-vault/src/tars_vault/tools/scaffold_workspace.py && pass "generated index natural-language examples" || fail "index natural-language examples missing"
grep -qi "process everything in my inbox" mcp/tars-vault/src/tars_vault/tools/scaffold_workspace.py commands/README.md && pass "inbox natural-language example" || fail "inbox natural-language example missing"

for f in examples/pm-customer-call.md examples/eng-design-discussion.md examples/sales-discovery-call.md examples/README.md; do
  [ -f "$f" ] && pass "example exists: $f" || fail "missing example: $f"
done

grep -q "workspace_type" templates/install.yaml && pass "install has workspace_type" || fail "install missing workspace_type"
grep -q "workspace_path" templates/install.yaml && pass "install has workspace_path" || fail "install missing workspace_path"
grep -q "obsidian_enabled" templates/install.yaml && pass "install has obsidian flag" || fail "install missing obsidian flag"
grep -q "workspace_path" hooks/_common.py && pass "hooks read workspace_path" || fail "hooks not workspace-aware"
grep -q "workspace_path" mcp/tars-vault/src/tars_vault/server.py && pass "server checks workspace_path" || fail "server not workspace-aware"
grep -q "scaffold_workspace" mcp/tars-vault/src/tars_vault/server.py && pass "server exposes scaffold_workspace" || fail "scaffold_workspace schema missing"
grep -q "mcp__tars_vault__scaffold_workspace" skills/welcome/SKILL.md && pass "welcome uses deterministic scaffold" || fail "welcome does not use scaffold tool"
grep -q "What should TARS know to personalize" skills/welcome/SKILL.md && pass "welcome asks identity essentials" || fail "welcome identity prompt missing"
! grep -q "First thing you want TARS to help with" skills/welcome/SKILL.md && pass "welcome does not ask open-ended first use case" || fail "welcome still asks open-ended first use case"
grep -q "Try this now" skills/welcome/SKILL.md && pass "welcome offers guided first demo" || fail "welcome guided demo missing"
grep -q "local TARS helper is not connected" skills/welcome/SKILL.md commands/welcome.md && pass "welcome has nontechnical local-helper recovery" || fail "welcome helper recovery missing"
grep -q "Markdown files are" skills/welcome/SKILL.md && pass "welcome explains Markdown plainly" || fail "welcome Markdown explanation missing"
grep -q "If you don't know what Obsidian is" skills/welcome/SKILL.md && pass "welcome explains Obsidian plainly" || fail "welcome Obsidian explanation missing"
grep -q "Never create generic product-management folders" skills/welcome/SKILL.md && pass "welcome forbids generic workspace folders" || fail "welcome generic-folder guard missing"
grep -q "Sonnet or a stronger model" CLAUDE.md && pass "runtime contract sets Sonnet-or-stronger setup expectation" || fail "Sonnet setup expectation missing"
! grep -qi "Haiku" CLAUDE.md skills/welcome/SKILL.md && pass "welcome setup no longer promises Haiku support" || fail "Haiku setup wording remains"
grep -q "mcp__tars_vault__scaffold_workspace" commands/welcome.md && pass "welcome command fallback uses scaffold" || fail "welcome command fallback missing scaffold"
grep -q "INBOX.md" commands/welcome.md && pass "welcome command forbids root inbox file" || fail "welcome command inbox guard missing"
grep -q "commands/welcome.md" tests/validate-release-artifact.py && pass "artifact validation checks packaged commands" || fail "artifact command validation missing"
grep -q "claude_home" hooks/pre-tool-use.py && pass "pre-tool blocks accidental ~/.claude writes" || fail "pre-tool ~/.claude guard missing"
grep -q "TARS Workspace" hooks/session-start.py skills/welcome/SKILL.md docs/GETTING-STARTED.md && pass "Documents workspace default documented" || fail "Documents workspace default missing"
[ -f scripts/migrate-install-record.py ] && pass "existing-user migration script exists" || fail "migration script missing"
grep -q "workspace_type" scripts/migrate-install-record.py && pass "migration backfills workspace_type" || fail "migration missing workspace_type"
grep -q "obsidian_enabled" scripts/migrate-install-record.py && pass "migration backfills obsidian flag" || fail "migration missing obsidian flag"
[ -f scripts/doctor.py ] && pass "runtime doctor exists" || fail "runtime doctor missing"
python3 scripts/doctor.py --workspace /tmp/tars-doctor-validation --json >/tmp/tars-doctor-validation.json 2>/tmp/tars-doctor-validation.err || true
python3 - <<'PY'
import json
data = json.load(open('/tmp/tars-doctor-validation.json'))
checks = {c.get('check') for c in data.get('checks', [])}
assert 'python' in checks and 'workspace_path' in checks and 'local_helper_transport' in checks
print('PASS  runtime doctor emits deterministic checks')
PY
[ $? -eq 0 ] || fail "runtime doctor output invalid"
grep -q "fastembed" requirements-search.txt && pass "optional search requirements separated" || fail "requirements-search missing fastembed"
! grep -q "fastembed" requirements.txt && pass "required requirements exclude optional FastEmbed" || fail "requirements.txt still requires FastEmbed"
! grep -q "mcp>=" requirements.txt && pass "first setup has no required mcp pip dependency" || fail "requirements.txt still requires mcp"

grep -q -- "--enable-obsidian" skills/welcome/SKILL.md && pass "enable Obsidian mode documented" || fail "enable Obsidian missing"
grep -q -- "--disable-obsidian" skills/welcome/SKILL.md && pass "disable Obsidian mode documented" || fail "disable Obsidian missing"
grep -q -- "--relocate" skills/welcome/SKILL.md && pass "relocate mode documented" || fail "relocate missing"
grep -q -- "--change-persona" skills/welcome/SKILL.md && pass "change persona mode documented" || fail "change persona missing"
grep -q "Do not re-scaffold" skills/welcome/SKILL.md && pass "relocate avoids rescaffold" || fail "relocate rescaffold guard missing"
grep -q "Existing identity, memory, schedule, and integrations were left untouched" skills/welcome/SKILL.md && pass "persona preserves state" || fail "persona preservation missing"

grep -q "coaching:" _system/maturity.yaml && pass "maturity has coaching state" || fail "coaching state missing"
grep -q "deferred_setup:" _system/maturity.yaml && pass "maturity has deferred setup state" || fail "deferred setup state missing"
grep -q "Next useful thing" skills/briefing/SKILL.md && pass "briefing coaching slot" || fail "briefing coaching missing"
grep -q -- "--continue-setup" skills/briefing/SKILL.md && pass "briefing deferred setup reminder" || fail "briefing deferred setup reminder missing"
grep -q "Empty-workspace response" skills/answer/SKILL.md && pass "answer empty-workspace coaching" || fail "answer empty-workspace missing"
grep -q "embedding model" skills/answer/SKILL.md && pass "FastEmbed warning" || fail "FastEmbed warning missing"

grep -q "Degradation messaging convention" skills/core/SKILL.md && pass "degradation convention" || fail "degradation convention missing"
for s in answer briefing meeting tasks create maintain; do
  grep -qi "degradation messaging convention" "skills/$s/SKILL.md" \
    && pass "$s references degradation convention" \
    || fail "$s missing degradation convention"
done

grep -q "\"query\"" mcp/tars-vault/src/tars_vault/server.py && pass "search_by_tag schema has query" || fail "search_by_tag query schema missing"
grep -q "\"frontmatter\"" mcp/tars-vault/src/tars_vault/server.py && pass "search_by_tag schema has frontmatter" || fail "search_by_tag frontmatter schema missing"
grep -q "\"dry_run\"" mcp/tars-vault/src/tars_vault/server.py && pass "archive_note schema has dry_run" || fail "archive dry_run schema missing"
grep -q "recent_backlink" mcp/tars-vault/src/tars_vault/tools/archive_note.py && pass "archive backlink guardrail" || fail "archive backlink guardrail missing"
grep -q "active_task_reference" mcp/tars-vault/src/tars_vault/tools/archive_note.py && pass "archive task guardrail" || fail "archive task guardrail missing"

for f in mcp/tars-vault/src/tars_vault/wikilink_pass.py mcp/tars-vault/src/tars_vault/organize.py; do
  if [ ! -f "$f" ]; then
    pass "$f absent until feature recovery"
  elif grep -qi -E "placeholder|skeleton|unimplemented" "$f"; then
    fail "$f is still a stub"
  else
    pass "$f present and implemented"
  fi
done
[ ! -f mcp/tars-vault/src/tars_vault/obsidian_cli.py ] && pass "unused obsidian_cli removed" || fail "obsidian_cli remains"

remaining=$(grep -rn -i -E "casual.mode|casual/standard|standard.*casual|mode:.casual|engagement.mode" docs README.md skills templates 2>/dev/null | grep -v "removal of the casual/standard" || true)
[ -z "$remaining" ] && pass "stale casual mode refs purged" || { fail "stale casual refs remain"; echo "$remaining"; }

stale_indexes=$(grep -rn "_index.md" skills docs README.md commands 2>/dev/null | grep -v "No \`_index.md\` files" | grep -v "replaced \`_index.md\`" | grep -v "replace \`_index.md\`" || true)
[ -z "$stale_indexes" ] && pass "stale _index.md guidance purged" || { fail "stale _index.md guidance remains"; echo "$stale_indexes"; }

python3 - <<'PY'
import os, re, sys
cmds = {f[:-3] for f in os.listdir("commands") if f.endswith(".md") and f != "README.md"}
missing = []
for name in os.listdir("skills"):
    path = os.path.join("skills", name, "SKILL.md")
    if not os.path.isfile(path):
        continue
    text = open(path, encoding="utf-8").read()
    if "user-invocable: true" in text and name != "core" and name not in cmds:
        missing.append(name)
if missing:
    print(f"FAIL  user-invocable skills without commands: {missing}")
    sys.exit(1)
print("PASS  every user-invocable skill has a command")
PY
[ $? -eq 0 ] || FAIL=1

python3 tests/validate-framework-contracts.py \
  && pass "framework contract checks green" \
  || fail "framework contract checks failed"

if [ -d mcp/tars-vault/tests ]; then
  if python3 -c "import pytest" >/dev/null 2>&1; then
    (cd mcp/tars-vault && python3 -m pytest tests/ -q) \
      && pass "MCP pytest suite green" \
      || fail "MCP pytest suite failed"
  else
    (cd mcp/tars-vault && python3 tests/test_tools.py && python3 tests/test_search_index.py) \
      && pass "MCP stdlib tests green" \
      || fail "MCP stdlib tests failed"
  fi
fi

python3 tests/test_real_world_smoke.py \
  && pass "real-world fresh install smoke green" \
  || fail "real-world fresh install smoke failed"

if [ -f tars-cowork-plugin/Archive.zip ]; then
  python3 tests/validate-release-artifact.py tars-cowork-plugin/Archive.zip \
    && pass "release artifact validation green" \
    || fail "release artifact validation failed"
else
  echo "SKIP  release artifact validation (run ./build-plugin.sh first)"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
  exit 0
fi

echo "ONE OR MORE CHECKS FAILED"
exit 1

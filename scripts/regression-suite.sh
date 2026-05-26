#!/usr/bin/env bash
# PRD-18 regression suite — release gate.
#
# Runs every layer of validation a release agent must pass. Prints a summary
# and writes machine-readable JSON to tests/regression/last-run.json.
#
# Layers implemented (subset of PRD-18; the rest are run as part of the
# layered CI workflows):
#
#   1. tests/run-all.sh --full           (existing structural validators)
#   2. mcp/tars-vault pytest             (MCP server unit tests)
#   3. scenario_matrix                   (SessionStart against 9 scenarios)
#   4. adversarial probes                (PRD-04/05/06/07/15/16/17 contracts)
#   5. perf gate                         (SessionStart <300ms median)
#   6. notice-string lint                (already in run-all.sh; re-asserted)
#   7. qa_reverify                       (every C*/M* finding from the audit)
#
# Layers not run from this shell script (run separately):
#   - cross-platform (CI matrix)
#   - happy-path slash-command smoke (real Claude session, manual)
#
# Usage:
#   scripts/regression-suite.sh [--quiet]
#
# Exits non-zero if any layer fails.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

QUIET=false
for arg in "$@"; do
    case "$arg" in
        --quiet) QUIET=true ;;
    esac
done

OUT_DIR="$REPO_ROOT/tests/regression"
mkdir -p "$OUT_DIR"
RESULT_FILE="$OUT_DIR/last-run.json"
TS="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
LIVE_VERSION="$(python3 -c 'import json,pathlib;print(json.loads(pathlib.Path(".claude-plugin/plugin.json").read_text())["version"])')"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_PYTHON="${VENV_PYTHON:-/private/tmp/tars-pytest-venv/bin/python}"

declare -a LAYER_NAMES
declare -a LAYER_RESULTS
OVERALL_RC=0

run_layer() {
    local label="$1"; shift
    local cmd_str="$*"
    local log="$OUT_DIR/layer-$(echo "$label" | tr '/[:upper:] ' '___' | tr -cd '[:alnum:]_').log"
    echo "─── [$label] $cmd_str"
    local start_ts; start_ts=$(date +%s)
    set +e
    bash -c "$cmd_str" >"$log" 2>&1
    local rc=$?
    set -e
    local end_ts; end_ts=$(date +%s)
    LAYER_NAMES+=("$label")
    if [[ $rc -eq 0 ]]; then
        LAYER_RESULTS+=("pass:$((end_ts - start_ts)):$log:0")
        echo "    ✓ PASS ($((end_ts - start_ts))s)"
    else
        LAYER_RESULTS+=("fail:$((end_ts - start_ts)):$log:$rc")
        echo "    ✗ FAIL ($((end_ts - start_ts))s, rc=$rc) — see $log"
        OVERALL_RC=1
    fi
}

echo "════════════════════════════════════════"
echo " TARS Regression Suite"
echo "════════════════════════════════════════"
echo "  version  : $LIVE_VERSION"
echo "  timestamp: $TS"
echo "  results  : $RESULT_FILE"
echo ""

run_layer "L1 run-all" "bash tests/run-all.sh --full"

if [[ -x "$VENV_PYTHON" ]]; then
    run_layer "L2 mcp pytest" "( cd mcp/tars-vault && $VENV_PYTHON -m pytest tests/ -q )"
elif "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
    run_layer "L2 mcp pytest" "( cd mcp/tars-vault && $PYTHON_BIN -m pytest tests/ -q )"
else
    run_layer "L2 mcp tests (stdlib)" "( cd mcp/tars-vault && $PYTHON_BIN tests/run_stdlib_suite.py )"
fi

run_layer "L3 scenarios" \
    "$PYTHON_BIN -m tests.regression.run_scenario_matrix --rescaffold > $OUT_DIR/scenarios.json"

run_layer "L4 adversarial" \
    "$PYTHON_BIN -m tests.regression.run_adversarial_probes > $OUT_DIR/adversarial.json"

run_layer "L5 perf" \
    "$PYTHON_BIN -m tests.regression.run_perf_gates > $OUT_DIR/perf.json"

run_layer "L6 notice-strings" "$PYTHON_BIN tests/test_notice_strings.py"

run_layer "L7 qa-reverify" \
    "$PYTHON_BIN -m tests.regression.run_qa_reverify > $OUT_DIR/qa-reverify.json"

python3 - "$RESULT_FILE" "$TS" "$LIVE_VERSION" "$OVERALL_RC" \
        "${LAYER_NAMES[@]}" "----" "${LAYER_RESULTS[@]}" <<'PY'
import json, sys, pathlib
out_path, ts, version, rc_str = sys.argv[1:5]
rest = sys.argv[5:]
sep = rest.index("----")
names = rest[:sep]
results = rest[sep+1:]
layers = []
for name, raw in zip(names, results):
    parts = raw.split(":")
    status = parts[0]
    seconds = int(parts[1])
    log = parts[2] if len(parts) > 2 else ""
    rc_layer = int(parts[3]) if len(parts) > 3 else 0
    layers.append({"name": name, "status": status, "seconds": seconds,
                   "log": log, "rc": rc_layer})
report = {
    "timestamp": ts,
    "plugin_version": version,
    "blocker": rc_str != "0",
    "layers": layers,
}
pathlib.Path(out_path).write_text(json.dumps(report, indent=2))
print()
print("════════════════════════════════════════")
print(" Summary")
print("════════════════════════════════════════")
for L in layers:
    icon = "✓" if L["status"] == "pass" else "✗"
    print(f"  {icon} {L['name']:24s} {L['status']:5s} {L['seconds']}s")
print()
print(f"  blocker: {report['blocker']}")
print(f"  json   : {out_path}")
PY

exit $OVERALL_RC

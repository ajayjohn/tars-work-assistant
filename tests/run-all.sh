#!/usr/bin/env bash
# TARS Plugin Test Runner
# Usage: ./tests/run-all.sh [--full]
# Compatible with the default macOS Bash 3 runtime.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ALL_TESTS="structure frontmatter references routing templates scripts"

test_script_for() {
    case "$1" in
        structure) echo "validate-structure.py" ;;
        frontmatter) echo "validate-frontmatter.py" ;;
        references) echo "validate-references.py" ;;
        routing) echo "validate-routing.py" ;;
        templates) echo "validate-templates.py" ;;
        scripts) echo "validate-scripts.py" ;;
        *) return 1 ;;
    esac
}

contains_word() {
    case " $1 " in
        *" $2 "*) return 0 ;;
        *) return 1 ;;
    esac
}

add_test() {
    if ! contains_word "$TESTS_TO_RUN" "$1"; then
        TESTS_TO_RUN="$TESTS_TO_RUN $1"
    fi
}

FULL_RUN=false
VERBOSE=false
for arg in "$@"; do
    case "$arg" in
        --full) FULL_RUN=true ;;
        --verbose|-v) VERBOSE=true ;;
        --help|-h)
            echo "Usage: $0 [--full] [--verbose]"
            echo ""
            echo "Options:"
            echo "  --full     Run all tests regardless of git changes"
            echo "  --verbose  Show detailed output from each test"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  TARS Plugin Test Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

TESTS_TO_RUN=""

if [ "$FULL_RUN" = true ]; then
    echo -e "${YELLOW}Mode: Full run (all tests)${NC}"
    echo ""
    TESTS_TO_RUN="$ALL_TESTS"
else
    echo -e "${YELLOW}Mode: Dynamic (git-diff based)${NC}"

    cd "$PLUGIN_ROOT"
    CHANGED_FILES=""

    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        CHANGED_FILES="$(git diff --name-only HEAD 2>/dev/null || true)"
        CHANGED_FILES="$CHANGED_FILES
$(git diff --name-only --cached 2>/dev/null || true)"
        CHANGED_FILES="$CHANGED_FILES
$(git ls-files --others --exclude-standard 2>/dev/null || true)"
    fi

    if [ -z "$(echo "$CHANGED_FILES" | tr -d '[:space:]')" ]; then
        echo "  No git changes detected. Running all tests as fallback."
        echo ""
        TESTS_TO_RUN="$ALL_TESTS"
    else
        while IFS= read -r file; do
            [ -z "$file" ] && continue
            case "$file" in
                skills/*)
                    add_test frontmatter
                    add_test references
                    add_test routing
                    ;;
                commands/*)
                    add_test structure
                    add_test references
                    ;;
                scripts/*)
                    add_test scripts
                    ;;
                reference/*)
                    add_test templates
                    ;;
                .claude-plugin/*|*plugin.json)
                    add_test structure
                    add_test references
                    ;;
            esac
        done <<EOF
$CHANGED_FILES
EOF

        if [ -z "$(echo "$TESTS_TO_RUN" | tr -d '[:space:]')" ]; then
            echo "  No matching tests for changed files. Running all tests."
            echo ""
            TESTS_TO_RUN="$ALL_TESTS"
        else
            echo "  Selected tests based on changes:$TESTS_TO_RUN"
            echo ""
        fi
    fi
fi

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_TESTS=""

for test_name in $ALL_TESTS; do
    test_script="$(test_script_for "$test_name")"
    test_path="$SCRIPT_DIR/$test_script"

    if [ ! -f "$test_path" ]; then
        echo -e "  ${YELLOW}SKIP${NC} $test_name ($test_script not found)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    if ! contains_word "$TESTS_TO_RUN" "$test_name"; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${YELLOW}SKIP${NC} $test_name (no matching changes)"
        fi
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    echo -e "  ${BLUE}RUN ${NC} $test_name..."

    set +e
    if [ "$VERBOSE" = true ]; then
        python3 "$test_path"
        EXIT_CODE=$?
        OUTPUT=""
    else
        OUTPUT="$(python3 "$test_path" 2>&1)"
        EXIT_CODE=$?
    fi
    set -e

    if [ "$EXIT_CODE" -eq 0 ]; then
        echo -e "  ${GREEN}PASS${NC} $test_name"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED}FAIL${NC} $test_name"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_TESTS="$FAILED_TESTS $test_name"
        if [ "$VERBOSE" = false ] && [ -n "$OUTPUT" ]; then
            echo ""
            echo "$OUTPUT" | sed 's/^/    /'
            echo ""
        fi
    fi
done

echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Results${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASS_COUNT"
echo -e "  ${RED}Failed:${NC}  $FAIL_COUNT"
echo -e "  ${YELLOW}Skipped:${NC} $SKIP_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "  ${RED}Failed tests:${NC}"
    for test_name in $FAILED_TESTS; do
        echo -e "    ${RED}x${NC} $test_name"
    done
    echo ""
    echo -e "  ${RED}STATUS: FAIL${NC}"
    exit 1
fi

echo -e "  ${GREEN}STATUS: ALL TESTS PASSED${NC}"
exit 0

#!/usr/bin/env bash
# TARS Plugin Test Runner
# Usage: ./tests/run-all.sh [--full]
# Without --full: runs tests dynamically based on git diff (changed files)
# With --full: runs all tests regardless of changes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test registry: maps test names to scripts
declare -A TESTS
TESTS[structure]="validate-structure.py"
TESTS[frontmatter]="validate-frontmatter.py"
TESTS[references]="validate-references.py"
TESTS[routing]="validate-routing.py"
TESTS[templates]="validate-templates.py"
TESTS[scripts]="validate-scripts.py"

# File pattern -> test mapping for dynamic selection
# Each pattern maps to space-separated test names
declare -A FILE_TEST_MAP
FILE_TEST_MAP["skills/"]="frontmatter references routing"
FILE_TEST_MAP["commands/"]="structure references"
FILE_TEST_MAP["scripts/"]="scripts"
FILE_TEST_MAP["reference/"]="templates"
FILE_TEST_MAP["plugin.json"]="structure references"
FILE_TEST_MAP[".claude-plugin/"]="structure references"

# Parse arguments
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

# Determine which tests to run
declare -A TESTS_TO_RUN

if [ "$FULL_RUN" = true ]; then
    echo -e "${YELLOW}Mode: Full run (all tests)${NC}"
    echo ""
    for test_name in "${!TESTS[@]}"; do
        TESTS_TO_RUN[$test_name]=1
    done
else
    echo -e "${YELLOW}Mode: Dynamic (git-diff based)${NC}"

    # Get changed files from git diff
    cd "$PLUGIN_ROOT"
    CHANGED_FILES=""

    if git rev-parse --is-inside-work-tree &>/dev/null; then
        # Get both staged and unstaged changes, plus untracked files
        CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || true)
        CHANGED_FILES="$CHANGED_FILES"$'\n'$(git diff --name-only --cached 2>/dev/null || true)
        CHANGED_FILES="$CHANGED_FILES"$'\n'$(git ls-files --others --exclude-standard 2>/dev/null || true)
    fi

    if [ -z "$(echo "$CHANGED_FILES" | tr -d '[:space:]')" ]; then
        echo "  No git changes detected — running all tests as fallback"
        echo ""
        for test_name in "${!TESTS[@]}"; do
            TESTS_TO_RUN[$test_name]=1
        done
    else
        # Map changed files to tests
        while IFS= read -r file; do
            [ -z "$file" ] && continue
            for pattern in "${!FILE_TEST_MAP[@]}"; do
                if [[ "$file" == *"$pattern"* ]]; then
                    IFS=' ' read -ra test_names <<< "${FILE_TEST_MAP[$pattern]}"
                    for t in "${test_names[@]}"; do
                        TESTS_TO_RUN[$t]=1
                    done
                fi
            done
        done <<< "$CHANGED_FILES"

        if [ ${#TESTS_TO_RUN[@]} -eq 0 ]; then
            echo "  No matching tests for changed files — running all tests"
            echo ""
            for test_name in "${!TESTS[@]}"; do
                TESTS_TO_RUN[$test_name]=1
            done
        else
            echo "  Selected tests based on changes: ${!TESTS_TO_RUN[*]}"
            echo ""
        fi
    fi
fi

# Run selected tests
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
FAILED_TESTS=()

# Sort test names for consistent ordering
SORTED_TESTS=($(echo "${!TESTS[@]}" | tr ' ' '\n' | sort))

for test_name in "${SORTED_TESTS[@]}"; do
    test_script="${TESTS[$test_name]}"
    test_path="$SCRIPT_DIR/$test_script"

    if [ ! -f "$test_path" ]; then
        echo -e "  ${YELLOW}SKIP${NC} $test_name ($test_script not found)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    if [ -z "${TESTS_TO_RUN[$test_name]+x}" ]; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${YELLOW}SKIP${NC} $test_name (no matching changes)"
        fi
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    echo -e "  ${BLUE}RUN ${NC} $test_name..."

    # Run test and capture output
    set +e
    if [ "$VERBOSE" = true ]; then
        python3 "$test_path"
        EXIT_CODE=$?
    else
        OUTPUT=$(python3 "$test_path" 2>&1)
        EXIT_CODE=$?
    fi
    set -e

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "  ${GREEN}PASS${NC} $test_name"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "  ${RED}FAIL${NC} $test_name"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILED_TESTS+=("$test_name")
        # Show output for failed tests even in non-verbose mode
        if [ "$VERBOSE" = false ] && [ -n "${OUTPUT:-}" ]; then
            echo ""
            echo "$OUTPUT" | sed 's/^/    /'
            echo ""
        fi
    fi
done

# Summary
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Results${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $PASS_COUNT"
echo -e "  ${RED}Failed:${NC}  $FAIL_COUNT"
echo -e "  ${YELLOW}Skipped:${NC} $SKIP_COUNT"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "  ${RED}Failed tests:${NC}"
    for t in "${FAILED_TESTS[@]}"; do
        echo -e "    ${RED}✗${NC} $t"
    done
    echo ""
    echo -e "  ${RED}STATUS: FAIL${NC}"
    exit 1
else
    echo -e "  ${GREEN}STATUS: ALL TESTS PASSED${NC}"
    exit 0
fi

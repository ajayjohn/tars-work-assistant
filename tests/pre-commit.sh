#!/usr/bin/env bash
# TARS Plugin Pre-Commit Hook
# Runs relevant validation tests before allowing a commit.
#
# Installation:
#   cp tests/pre-commit.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

set -euo pipefail

# Find plugin root (handle being called from .git/hooks/)
if [ -f "$(dirname "$0")/../../tests/run-all.sh" ]; then
    PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
elif [ -f "./tests/run-all.sh" ]; then
    PLUGIN_ROOT="$(pwd)"
else
    echo "Error: Cannot find TARS plugin root"
    exit 1
fi

TESTS_DIR="$PLUGIN_ROOT/tests"

echo "TARS Pre-Commit: Running validation..."
echo ""

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

if [ -z "$STAGED_FILES" ]; then
    echo "No staged files — skipping validation"
    exit 0
fi

# Determine which tests to run based on staged files
TESTS_TO_RUN=""

for file in $STAGED_FILES; do
    case "$file" in
        skills/*)
            TESTS_TO_RUN="$TESTS_TO_RUN frontmatter references routing"
            ;;
        commands/*)
            TESTS_TO_RUN="$TESTS_TO_RUN structure references"
            ;;
        scripts/*)
            TESTS_TO_RUN="$TESTS_TO_RUN scripts"
            ;;
        reference/*)
            TESTS_TO_RUN="$TESTS_TO_RUN templates"
            ;;
        .claude-plugin/plugin.json|plugin.json)
            TESTS_TO_RUN="$TESTS_TO_RUN structure references"
            ;;
    esac
done

# Deduplicate
TESTS_TO_RUN=$(echo "$TESTS_TO_RUN" | tr ' ' '\n' | sort -u | tr '\n' ' ')

if [ -z "$(echo "$TESTS_TO_RUN" | tr -d '[:space:]')" ]; then
    echo "No relevant tests for staged files — skipping"
    exit 0
fi

echo "Running tests: $TESTS_TO_RUN"
echo ""

# Run each selected test
FAILED=0

for test_name in $TESTS_TO_RUN; do
    test_script="validate-${test_name}.py"
    test_path="$TESTS_DIR/$test_script"

    if [ ! -f "$test_path" ]; then
        echo "  SKIP $test_name ($test_script not found)"
        continue
    fi

    echo -n "  $test_name... "
    if python3 "$test_path" > /dev/null 2>&1; then
        echo "PASS"
    else
        echo "FAIL"
        FAILED=$((FAILED + 1))
        # Show output for failed test
        echo ""
        python3 "$test_path" 2>&1 | sed 's/^/    /'
        echo ""
    fi
done

echo ""

if [ $FAILED -gt 0 ]; then
    echo "Pre-commit check FAILED ($FAILED test(s) failed)"
    echo "Fix the issues above, then try committing again."
    echo ""
    echo "To skip this check (not recommended):"
    echo "  git commit --no-verify"
    exit 1
else
    echo "Pre-commit check PASSED"
    exit 0
fi

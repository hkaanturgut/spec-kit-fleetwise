#!/usr/bin/env bash
# Rehearses the sdd-autopilot workflow against a throwaway copy of this repo,
# using a stub Copilot CLI, and asserts which Spec Kit steps ran in each scenario.
#
# Requires: specify (Spec Kit CLI), git, python3, dotnet.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="$(mktemp -d)"
STUB_DIR="$WORK/bin"
export STUB_LOG="$WORK/calls.log"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$STUB_DIR"
cp "$REPO/tests/workflow/stub-copilot" "$STUB_DIR/copilot"
chmod +x "$STUB_DIR/copilot"
export PATH="$STUB_DIR:$PATH"

git -C "$REPO" ls-files -z | (cd "$REPO" && xargs -0 tar -cf -) | (mkdir -p "$WORK/repo" && tar -xf - -C "$WORK/repo")
cd "$WORK/repo"
git init -q -b main
git config user.email "ci@example.com"
git config user.name "ci"
git add -A && git commit -qm "baseline"

specify init --here --force --integration copilot --ignore-agent-tools >/dev/null
specify workflow add --dev ./workflows/sdd-autopilot >/dev/null

fail=0
run() { : > "$STUB_LOG"; specify workflow run sdd-autopilot "$@" < /dev/null > "$WORK/run.out" 2>&1 || true; }
calls() { paste -sd' ' "$STUB_LOG" 2>/dev/null || true; }
status() { grep -o 'Status: [a-z]*' "$WORK/run.out" | awk '{print $2}' | tail -1; }
expect() {
  local name="$1" want_calls="$2" want_status="$3"
  local got_calls got_status
  got_calls="$(calls)"; got_status="$(status)"
  if [[ "$got_calls" == "$want_calls" && "$got_status" == "$want_status" ]]; then
    echo "PASS  $name  [$got_status] $got_calls"
  else
    echo "FAIL  $name"; echo "      want [$want_status] $want_calls"; echo "      got  [$got_status] $got_calls"
    sed 's/^/      | /' "$WORK/run.out" | tail -15
    fail=1
  fi
}

# A: template constitution -> the run stops at the constitution gate.
run -i approval=approve
expect "A no constitution stops" "" "paused"

printf '# FleetWise Constitution\n\n## Principles\n\n1. Tenant isolation is mandatory.\n' > .specify/memory/constitution.md
git add -A && git commit -qm "constitution"

# B: empty feature, build until converged.
run -i until=converge -i approval=approve -i spec="Overdue dispatcher"
expect "B full run" "/speckit-specify /speckit-plan /speckit-tasks /speckit-analyze /speckit-implement /speckit-converge" "completed"
git add -A && git commit -qm "feature"

# C: spec changed -> only plan, tasks, analyze.
echo "- The overdue window is configurable per tenant (default 7 days)." >> specs/001-overdue-dispatcher/spec.md
run -i approval=approve
expect "C spec change reruns only stale steps" "/speckit-plan /speckit-tasks /speckit-analyze" "completed"
git add -A && git commit -qm "spec change"

# D: nothing changed -> only analyze (always runs) and the gate.
run -i approval=approve
expect "D nothing stale" "/speckit-analyze" "completed"

# F: successful commands alone must not stamp artifacts as reviewed.
cp specs/001-overdue-dispatcher/.sdd-stamps.json "$WORK/stamps-before.json"
echo "- Managers can review a tenant's window setting." >> specs/001-overdue-dispatcher/spec.md
run
expect "F no approval leaves artifacts stale" "/speckit-plan /speckit-tasks /speckit-analyze" "paused"
cmp "$WORK/stamps-before.json" specs/001-overdue-dispatcher/.sdd-stamps.json
python3 scripts/speckit_state.py state | python3 -c 'import json,sys; s=json.load(sys.stdin); assert s["plan_stale"] and s["tasks_stale"], s'

# E: open question in the spec -> pauses at the clarify gate before anything else.
echo "[NEEDS CLARIFICATION: who can approve a work order?]" >> specs/001-overdue-dispatcher/spec.md
run -i approval=approve
expect "E open question pauses for a human" "" "paused"

# Delivery wiring uses the real engine and command adapter, never real GitHub writes.
export DELIVERY_TEST=1
export DELIVERY_LOG="$WORK/delivery.log"
cat > scripts/workflow_github.py <<'PY'
import os
from pathlib import Path
import sys

action = sys.argv[1]
with open(os.environ["DELIVERY_LOG"], "a") as log:
    log.write(action + "\n")
if action == "issues":
    Path(".issues-created").touch()
if action == "verify-issues" and not Path(".issues-created").exists():
    sys.exit("Missing issue creation")
PY
cat > "$STUB_DIR/dotnet" <<'SH'
#!/usr/bin/env bash
echo test >> "$DELIVERY_LOG"
exit "${DELIVERY_TEST_EXIT:-0}"
SH
chmod +x "$STUB_DIR/dotnet"
run_delivery() {
  : > "$STUB_LOG"
  : > "$DELIVERY_LOG"
  rm -f .issues-created
  specify workflow run ./workflows/speckit-delivery/workflow.yml "$@" < /dev/null > "$WORK/run.out" 2>&1 || true
}
expect_delivery() {
  if [[ "$(paste -sd' ' "$DELIVERY_LOG")" != "$1" ]]; then
    echo "FAIL delivery shell sequence: $(paste -sd' ' "$DELIVERY_LOG")"
    fail=1
  fi
}
run_delivery -i spec="Health response"
expect "G delivery pauses at spec review" "/speckit-specify" "paused"
expect_delivery "prepare"

run_delivery -i spec="Health response" -i spec_review=approve -i plan_review=approve
expect "H delivery pauses before public issues" "/speckit-specify /speckit-plan /speckit-tasks" "paused"
expect_delivery "prepare"

run_delivery -i spec="Health response" -i spec_review=approve -i plan_review=approve -i issues_review=approve
expect "I delivery pauses before commit/push/PR" "/speckit-specify /speckit-plan /speckit-tasks /speckit-taskstoissues /speckit-implement" "paused"
expect_delivery "prepare issues verify-issues test review"

run_delivery -i spec="Health response" -i spec_review=approve -i plan_review=approve -i issues_review=approve -i publish_review=approve
expect "J delivery full pipeline" "/speckit-specify /speckit-plan /speckit-tasks /speckit-taskstoissues /speckit-implement" "completed"
expect_delivery "prepare issues verify-issues test review publish"

DELIVERY_TEST_EXIT=1 run_delivery -i spec="Health response" -i spec_review=approve -i plan_review=approve -i issues_review=approve -i publish_review=approve
expect "K failing tests prevent publication" "/speckit-specify /speckit-plan /speckit-tasks /speckit-taskstoissues /speckit-implement" "failed"
expect_delivery "prepare issues verify-issues test"

SKIP_ISSUES=1 run_delivery -i spec="Health response" -i spec_review=approve -i plan_review=approve -i issues_review=approve -i publish_review=approve
expect "L no-op issue command prevents implementation" "/speckit-specify /speckit-plan /speckit-tasks /speckit-taskstoissues" "failed"
expect_delivery "prepare verify-issues"

exit $fail

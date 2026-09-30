#!/usr/bin/env bash
# Full reset to the very start of the demo (legacy FleetWise, no Spec Kit).
# Usage: scripts/reset.sh            reset the local repo
#        scripts/reset.sh --github   also close open issues and PRs labelled "demo"
set -euo pipefail
# A checkpoint changes this script too, so finish the reset from a temporary copy.
if [[ -z "${RESET_REEXEC:-}" ]]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  tmp="$(mktemp)"
  cp "$0" "$tmp"
  RESET_REEXEC=1 RESET_ROOT="$ROOT" RESET_TEMP="$tmp" exec bash "$tmp" "$@"
fi
if [[ -n "${RESET_TEMP:-}" ]]; then trap 'rm -f "$RESET_TEMP"' EXIT; fi
cd "$RESET_ROOT"

git fetch -q --tags 2>/dev/null || true
bash scripts/jump.sh s1-00-start
git clean -fdxq -e .vscode
rm -f src/FleetWise.Api/fleetwise.db*

if [[ "${1:-}" == "--github" ]]; then
  for pr in $(gh pr list --label demo --state open --json number -q '.[].number'); do gh pr close "$pr" --delete-branch; done
  for issue in $(gh issue list --label demo --state open --json number -q '.[].number'); do gh issue close "$issue"; done
fi

dotnet build --nologo -v q
echo "Reset complete: branch demo-live at s1-00-start. Next: scripts/preflight.sh"

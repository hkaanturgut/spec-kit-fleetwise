#!/usr/bin/env bash
# Full reset to the very start of the demo (legacy FleetWise, no Spec Kit).
# Usage: scripts/reset.sh            reset the local repo
#        scripts/reset.sh --github   also close open issues and PRs labelled "demo"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

git fetch -q --tags 2>/dev/null || true
git switch -q -C demo-live s1-00-start
git clean -fdxq -e .vscode
rm -f src/FleetWise.Api/fleetwise.db*

if [[ "${1:-}" == "--github" ]]; then
  for pr in $(gh pr list --label demo --state open --json number -q '.[].number'); do gh pr close "$pr" --delete-branch; done
  for issue in $(gh issue list --label demo --state open --json number -q '.[].number'); do gh issue close "$issue"; done
fi

dotnet build --nologo -v q >/dev/null
echo "Reset complete: branch demo-live at s1-00-start. Next: scripts/preflight.sh"

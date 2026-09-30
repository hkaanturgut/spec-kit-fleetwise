#!/usr/bin/env bash
# Green/red readiness check before going on stage.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
PINNED="$(tr -d '[:space:]' < .speckit-version)"
failures=0

ok()   { printf '  \033[32mOK\033[0m    %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; failures=$((failures + 1)); }
warn() { printf '  \033[33mWARN\033[0m  %s\n' "$1"; }

echo "Tools"
command -v git >/dev/null && ok "git" || bad "git missing"
command -v python3 >/dev/null && ok "python3" || bad "python3 missing"
if sdk="$(dotnet --version 2>&1)" && [[ "$sdk" == 8.* ]]; then
  ok "dotnet SDK $sdk (global.json resolved)"
else
  bad ".NET 8 SDK required by global.json is not available"
  printf '%s\n' "$sdk"
fi
if command -v specify >/dev/null; then
  if version="$(specify version 2>&1)" && grep -F "CLI Version    $PINNED " <<< "$version" >/dev/null; then ok "specify $PINNED"; else bad "specify is not v$PINNED (run scripts/install-tools.sh)"; printf '%s\n' "$version"; fi
else bad "specify missing (run scripts/install-tools.sh)"; fi
command -v copilot >/dev/null && ok "copilot CLI (needed for workflow runs)" || warn "copilot CLI missing: workflow segment will need the recording"
if command -v gh >/dev/null && login="$(gh api user --jq .login 2>&1)"; then
  ok "gh authenticated as $login"
else
  warn "gh authentication unavailable (needed for issues and PRs)"
  printf '%s\n' "${login:-gh CLI missing}"
fi

echo "Repo"
git rev-parse -q --verify refs/tags/s1-00-start >/dev/null && ok "tag s1-00-start" || bad "tag s1-00-start missing"
[[ -z "$(git status --porcelain)" ]] && ok "working tree clean" || warn "working tree has changes (run scripts/reset.sh)"
count=$(git tag --list 's1-*' | wc -l | tr -d ' ')
[[ "$count" -ge 8 ]] && ok "$count checkpoint tags" || warn "only $count checkpoint tags (dry run not recorded yet?)"

echo "App"
if dotnet test --nologo -v q; then ok "dotnet test green"; else bad "dotnet test failing"; fi

echo
if [[ $failures -eq 0 ]]; then echo "Preflight: GREEN"; else echo "Preflight: $failures problem(s)"; exit 1; fi

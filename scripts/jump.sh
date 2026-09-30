#!/usr/bin/env bash
# Jump the demo to a checkpoint tag, discarding local changes.
# Usage: scripts/jump.sh <tag>      e.g. scripts/jump.sh s1-05-plan-tasks
#        scripts/jump.sh --list     show available checkpoints
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--list" || -z "${1:-}" ]]; then
  echo "Checkpoints:"
  git tag --list 's1-*' --sort=refname --format='  %(refname:short)  %(subject)'
  exit 0
fi

TAG="$1"
if ! git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  echo "Unknown checkpoint: $TAG (run scripts/jump.sh --list)" >&2
  exit 1
fi

git switch -q -C demo-live "$TAG"
git clean -fdq -e fleetwise.db
echo "Now at $TAG on branch demo-live."
if [[ -d .specify ]]; then
  python3 scripts/speckit_state.py explain || true
fi

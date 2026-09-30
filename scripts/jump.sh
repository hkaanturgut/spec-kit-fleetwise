#!/usr/bin/env bash
# Jump the demo to a checkpoint tag, discarding local changes.
# Usage: scripts/jump.sh <tag>      e.g. scripts/jump.sh s1-05-plan-tasks
#        scripts/jump.sh --list     show available checkpoints
set -euo pipefail

# Switching tags rewrites this file while it runs, so run from a temporary copy.
if [[ -z "${JUMP_REEXEC:-}" ]]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  tmp="$(mktemp)"
  cp "$0" "$tmp"
  JUMP_REEXEC=1 JUMP_ROOT="$ROOT" exec bash "$tmp" "$@"
fi
cd "$JUMP_ROOT"

if [[ "${1:-}" == "--list" || -z "${1:-}" ]]; then
  echo "Checkpoints:"
  git tag --list 's1-*' --sort=refname --format='  %(refname:short)  %(contents:subject)'
  exit 0
fi

TAG="$1"
if ! git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  echo "Unknown checkpoint: $TAG (run scripts/jump.sh --list)" >&2
  exit 1
fi

git switch -q -f -C demo-live "$TAG"
git clean -fdq -e fleetwise.db

# .specify/feature.json is gitignored (per machine), so a checkout never restores it.
# Point Spec Kit at the newest feature folder so /speckit-* commands keep working.
if [[ -d .specify && -d specs ]]; then
  latest="$(find specs -mindepth 1 -maxdepth 1 -type d | sort | tail -1)"
  if [[ -n "$latest" ]]; then
    printf '{"feature_directory":"%s"}\n' "$latest" > .specify/feature.json
  fi
fi

echo "Now at $TAG on branch demo-live."
if [[ -d .specify ]]; then
  python3 scripts/speckit_state.py explain || true
fi

#!/usr/bin/env bash
# Installs the pinned Spec Kit CLI so the demo never changes under you.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/.speckit-version")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

uv tool install --force specify-cli --from "git+https://github.com/github/spec-kit.git@v${VERSION}"
echo "Installed Spec Kit v${VERSION}. Check with: specify version"

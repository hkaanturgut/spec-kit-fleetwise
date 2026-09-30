#!/usr/bin/env bash
# Exercise destructive checkpoint commands only in a disposable local clone.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
git clone --quiet --no-hardlinks "$REPO" "$WORK/repo"
cd "$WORK/repo"
git switch -q -C main
git config user.name "Checkpoint test"
git config user.email "checkpoint-test@example.com"

files=(README.md scripts/jump.sh scripts/reset.sh scripts/preflight.sh workflows/sdd-autopilot/workflow.yml)
for file in "${files[@]}"; do cp "$REPO/$file" "$file"; done
git add -- "${files[@]}"
git commit -qm "Test current presentation tooling" --allow-empty
git for-each-ref --format='%(refname) %(objectname)' 'refs/tags/s1-*' > "$WORK/tags-before"
[[ "$(wc -l < "$WORK/tags-before" | tr -d ' ')" == 8 ]]

mkdir -p "$WORK/bin"
cat > "$WORK/bin/dotnet" <<'SH'
#!/usr/bin/env bash
echo "$*" >> "${BUILD_LOG:?}"
exit "${TEST_DOTNET_EXIT:-0}"
SH
chmod +x "$WORK/bin/dotnet"
export PATH="$WORK/bin:$PATH"
export BUILD_LOG="$WORK/build.log"

check_presentation() {
  local file
  for file in "${files[@]}"; do
    git show "main:$file" | cmp - "$file"
  done
}

bash scripts/reset.sh > "$WORK/reset.out" 2>&1 || { cat "$WORK/reset.out"; exit 1; }
check_presentation
[[ "$(git rev-parse HEAD)" == "$(git rev-parse 's1-00-start^{commit}')" ]]
grep -Fx 'build --nologo -v q' "$BUILD_LOG" >/dev/null

count=0
while IFS= read -r tag; do
  echo "Unsaved presentation edit" >> README.md
  bash scripts/jump.sh "$tag" > "$WORK/jump.out" 2>&1 || { cat "$WORK/jump.out"; exit 1; }
  [[ "$(git rev-parse HEAD)" == "$(git rev-parse "$tag^{commit}")" ]]
  check_presentation
  if [[ -d specs ]]; then
    python3 - <<'PY'
import json
from pathlib import Path
latest = sorted(p for p in Path("specs").iterdir() if p.is_dir())[-1]
assert json.loads(Path(".specify/feature.json").read_text())["feature_directory"] == str(latest)
PY
  fi
  echo "PASS $tag: current README/tooling and checkpoint HEAD"
  count=$((count + 1))
done < <(git tag --list 's1-*' --sort=refname)
[[ "$count" == 8 ]]

before="$(git status --porcelain)"
if bash scripts/jump.sh missing-checkpoint > "$WORK/invalid.out" 2>&1; then
  echo "Unknown checkpoint unexpectedly succeeded" >&2
  exit 1
fi
[[ "$(git status --porcelain)" == "$before" ]]

# Reset must work after a jump has restored newer presentation files.
echo "Unsaved practice change" >> README.md
bash scripts/reset.sh > "$WORK/reset.out" 2>&1 || { cat "$WORK/reset.out"; exit 1; }
check_presentation
[[ ! -d .specify ]]
git for-each-ref --format='%(refname) %(objectname)' 'refs/tags/s1-*' > "$WORK/tags-after"
cmp "$WORK/tags-before" "$WORK/tags-after"

if TEST_DOTNET_EXIT=1 bash scripts/reset.sh > "$WORK/reset.out" 2>&1; then
  echo "Reset masked a build failure" >&2
  exit 1
fi
echo "PASS repeated reset, feature pointer, invalid tag, immutable tags, and build failure"

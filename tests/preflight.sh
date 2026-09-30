#!/usr/bin/env bash
# Exercise preflight failures without installing tools or contacting GitHub.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/scripts" "$WORK/bin"
cp "$REPO/scripts/preflight.sh" "$WORK/scripts/"
cp "$REPO/.speckit-version" "$WORK/"
cat > "$WORK/bin/specify" <<'PY'
#!/usr/bin/env python3
import os
import sys
print("CLI Version    " + os.environ.get("TEST_SPECIFY_VERSION", "1.0.13") + " ")
sys.stdout.flush()
for _ in range(10000):
    print("Remaining version output")
PY
cat > "$WORK/bin/dotnet" <<'SH'
#!/usr/bin/env bash
case "$1" in
  --version)
    if [[ "${TEST_SDK_MISSING:-0}" == 1 ]]; then
      echo "SDK required by global.json is unavailable" >&2
      exit 1
    fi
    echo 8.0.414 ;;
  --list-sdks) echo '8.0.100 [installed but below the required feature band]' ;;
  test) echo 'Test output'; exit "${TEST_FAILURE:-0}" ;;
  *) exit 1 ;;
esac
SH
cat > "$WORK/bin/gh" <<'SH'
#!/usr/bin/env bash
if [[ "$1" == api ]]; then echo demo-user; else exit 1; fi
SH
cat > "$WORK/bin/git" <<'SH'
#!/usr/bin/env bash
case "$1" in
  rev-parse|status) exit 0 ;;
  tag) printf 's1-%s\n' 00 01 02 03 04 05 06 07 ;;
  *) exit 1 ;;
esac
SH
chmod +x "$WORK/bin/specify" "$WORK/bin/dotnet" "$WORK/bin/gh" "$WORK/bin/git"
export PATH="$WORK/bin:$PATH"

check() {
  local expected="$1" message="$2" actual=0
  shift 2
  env "$@" bash "$WORK/scripts/preflight.sh" > "$WORK/out" 2>&1 || actual=$?
  if [[ "$actual" != "$expected" ]] || ! grep -F "$message" "$WORK/out" >/dev/null; then
    cat "$WORK/out"
    echo "Expected exit $expected and message: $message" >&2
    exit 1
  fi
}

check 0 "Preflight: GREEN"
check 0 "gh authenticated as demo-user"
check 1 "global.json is not available" TEST_SDK_MISSING=1
check 1 "specify is not v1.0.13" TEST_SPECIFY_VERSION=1.0.130
check 1 "dotnet test failing" TEST_FAILURE=1
echo "PASS preflight: complete version output, SDK resolution, wrong version, test failure"

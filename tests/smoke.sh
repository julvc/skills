#!/usr/bin/env bash
# Smoke test: installs SnapDoczilla into a throwaway repo and checks the whole pipeline.
# Run from anywhere: bash tests/smoke.sh   (needs git, python3, curl)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*"; exit 1; }
build() { bash documentation/update.sh --html-only >/dev/null 2>&1; }

cd "$T"
git init -q; git config user.email smoke@test; git config user.name smoke
git remote add origin git@github.com:acme/shop.git
mkdir -p src; echo 'export const sum = (a, b) => a + b;' > src/sum.js
git add -A; git commit -qm init

echo "1. install"
bash "$HERE/skills/snapdoczilla/scripts/install.sh" "$T" "Smoke" en >/dev/null
bash "$HERE/skills/snapdoczilla/scripts/install.sh" "$T" "Smoke" en >/dev/null 2>&1 && fail "second install must refuse"
grep -q 'repo_url: https://github.com/acme/shop$' documentation/mkdocs.yml || fail "repo_url from SSH remote"
grep -q "edit_uri: edit/$(git symbolic-ref --short HEAD)/documentation/source/" documentation/mkdocs.yml || fail "edit_uri"
grep -q 'language: en' documentation/mkdocs.yml || fail "language"
grep -q 'English' documentation/AGENT-RULES.md || fail "language in agent rules"
[ -s documentation/source/assets/mermaid.min.js ] || fail "mermaid not downloaded"

echo "2. build with real code + diagram"
cat > documentation/source/sum.md <<'EOF'
# sum

```mermaid
flowchart LR
  a --> b
```

```js
--8<-- "src/sum.js"
```
EOF
sed -i 's|  - Home: index.md|&\n  - Sum: sum.md|' documentation/mkdocs.yml
build || fail "build"
grep -q 'sum' documentation/html/sum.html && grep -q '=&gt;' documentation/html/sum.html || fail "snippet not embedded"
grep -q 'class="diagram"' documentation/html/sum.html || fail "mermaid fence"

echo "3. strict build rejects mistakes and keeps the previous html/"
echo '# orphan' > documentation/source/orphan.md
build && fail "page outside nav must fail"
rm documentation/source/orphan.md
echo '[broken](missing.md)' >> documentation/source/sum.md
build && fail "broken link must fail"
sed -i '$d' documentation/source/sum.md
mv src/sum.js src/moved.js
build && fail "missing snippet must fail"
mv src/moved.js src/sum.js
[ -f documentation/html/sum.html ] || fail "a failed build emptied html/"
build || fail "build after fixes"

echo "4. agent step (DOCS_LLM) and sync marker"
DOCS_LLM="echo" bash documentation/update.sh --code >/dev/null || fail "DOCS_LLM path"
[ "$(cat documentation/.last-sync-code)" = "$(git rev-parse HEAD)" ] || fail "sync marker"
bash documentation/update.sh --nope >/dev/null 2>&1 && fail "unknown option must fail"

echo "5. pre-push reminder"
git add -A; git commit -qm docs
git rev-parse HEAD > documentation/.last-sync-code
echo '// change' >> src/sum.js; git add -A; git commit -qm change
bash .githooks/pre-push 2>&1 | grep -q 'Docs reminder (code): 1' || fail "hook reminder"

echo "All smoke checks passed"

#!/usr/bin/env bash
# Rough token cost of reading code in full: estimate.sh <repo-root> [path ...]   (default path: .)
# ponytail: ~4 bytes/token, tracked text files only (images/lockfiles/minified skipped); a guide, not a meter
set -euo pipefail
cd "${1:?usage: estimate.sh <repo-root> [path ...]}"; shift
[ $# -gt 0 ] || set -- .
for p in "$@"; do
  read -r n b < <(git ls-files -z -- "$p" ':!documentation' ':!*.png' ':!*.jpg' ':!*.gif' ':!*.svg' ':!*.ico' ':!*.lock' ':!*-lock.json' ':!*.min.js' ':!*.map' \
    | xargs -0 -r wc -c 2>/dev/null | awk '$2!="total"{n++;b+=$1} END{print n+0,b+0}')
  echo "$p: $n files, ~$((b/4000))k tokens if read in full"
done

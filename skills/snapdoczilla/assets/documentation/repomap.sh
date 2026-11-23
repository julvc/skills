#!/usr/bin/env bash
# Cheap repo map, reads no code: repomap.sh <repo-root> [path ...]   (default path: .)
# Per path: analyzable size (~tokens), what ignore.conf omits, top folders, manifests, entrypoint candidates.
# ponytail: ~4 bytes/token and name-based entrypoints; a guide to start from, not a parser
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${1:?usage: repomap.sh <repo-root> [path ...]}"; shift
[ $# -gt 0 ] || set -- .
IGN="$PWD/documentation/ignore.conf"; [ -f "$IGN" ] || IGN="$HERE/ignore.conf"
PATS=(); while IFS= read -r l; do PATS+=("$l"); done < <(grep -vE '^[[:space:]]*(#|$)' "$IGN")
EX=(); for p in "${PATS[@]}"; do EX+=(":!$p"); done

for p in "$@"; do
  K() { git ls-files "$@" -- "$p" ':!documentation' "${EX[@]}"; }   # analyzable files
  ALL="$(git ls-files -- "$p" ':!documentation')"
  KEPT="$(K)"; H() { echo "$KEPT" | grep . || true; }   # git is slow on Windows: list once
  kept="$(H | wc -l)"; total="$(echo "$ALL" | grep -c . || true)"
  bytes="$(K -z | xargs -0 -r wc -c 2>/dev/null | awk '$2!="total"{b+=$1} END{print b+0}')"
  echo "== $p: $kept files to analyze (~$((bytes / 4000))k tokens if read in full), $((total - kept)) omitted by ignore.conf"
  # omitted files = all - analyzable; first matching pattern wins (case globs behave like git pathspecs: * crosses /)
  om="$(comm -23 <(echo "$ALL" | sort) <(echo "$KEPT" | sort) | while IFS= read -r f; do
    for pat in "${PATS[@]}"; do case "$f" in $pat) echo "$pat"; break ;; esac; done
  done | sort | uniq -c | awk '{printf " %s(%s)", $2, $1}')"
  [ -z "$om" ] || echo "omitted:$om"
  echo "top folders:"; H | awk -F/ 'NF>1{d=$1"/"$2} NF<=1{d="."} {c[d]++} END{for(d in c) print "  " c[d], d}' | sort -rn | head -15
  echo "manifests:"; H | grep -E '(^|/)(package\.json|pom\.xml|build\.gradle|requirements\.txt|pyproject\.toml|go\.mod|Cargo\.toml|[^/]+\.csproj)$' | sed 's/^/  /' | head -10 || true
  echo "entrypoint candidates:"; H | grep -E '(^|/)(main|index|app|server|routes?|router|controllers?|schema)[^/]*$' | sed 's/^/  /' | head -30 || true
done

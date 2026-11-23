#!/usr/bin/env bash
# SnapDoczilla: (1) an agent CLI updates documentation/source from the code that changed,
# (2) the HTML site in documentation/html is rebuilt.
#   ./documentation/update.sh               -> every area in areas.conf: agent + HTML
#   ./documentation/update.sh --<area>      -> one area only (e.g. --front)
#   ./documentation/update.sh --html-only   -> HTML only (after editing .md by hand; no agent)
#   --full   first run of an area: read all of it (default is a small MVP)
#   --yes    accept the token cost without asking (guard limit: DOCS_MAX_TOKENS, default 50000)
# Agent: Claude Code by default. Another one: DOCS_LLM="codex exec --full-auto" | "opencode run" | "gemini --yolo -p"
# (any non-interactive command that takes the prompt as its last argument).
set -euo pipefail

DOC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$DOC_DIR" rev-parse --show-toplevel)"
CONF="$DOC_DIR/areas.conf"
[ -f "$CONF" ] || { echo "ERROR: missing $CONF"; exit 1; }

# "name=path" lines, without comments or blanks
LINES="$(grep -v -E '^[[:space:]]*(#|$)' "$CONF")"
ALL="$(echo "$LINES" | cut -d= -f1)"
path_of() { echo "$LINES" | grep -E "^$1=" | head -1 | cut -d= -f2-; }

AREAS="$ALL"; HTML_ONLY=0; FULL=0; YES=0
for a in "$@"; do
  if [ "$a" = "--html-only" ]; then HTML_ONLY=1
  elif [ "$a" = "--full" ]; then FULL=1
  elif [ "$a" = "--yes" ]; then YES=1
  elif echo "$ALL" | grep -qx -- "${a#--}"; then AREAS="${a#--}"
  else echo "Unknown option: $a (areas: $(echo $ALL | tr '\n' ' '), --html-only)"; exit 1
  fi
done

# --- 1. Agent: incremental update since the last documented commit of each area ---
if [ "$HTML_ONLY" -eq 0 ]; then
  LLM="${DOCS_LLM:-claude}"
  command -v "${LLM%% *}" >/dev/null || { echo "ERROR: '${LLM%% *}' not found. Install it, set DOCS_LLM or use --html-only."; exit 1; }
  for AREA in $AREAS; do
    AREA_PATH="$(path_of "$AREA")"
    STATE="$DOC_DIR/.last-sync-$AREA"
    RULES="documentation/AGENT-RULES.md"
    [ -f "$DOC_DIR/AGENT-RULES-$AREA.md" ] && RULES="$RULES and documentation/AGENT-RULES-$AREA.md"
    BASE="$(cat "$STATE" 2>/dev/null || echo "")"
    # Token guard: estimate (~4 bytes/token) what the agent may have to read; above DOCS_MAX_TOKENS ask first.
    if [ -n "$BASE" ]; then
      BYTES="$(git -C "$ROOT" diff "$BASE..HEAD" -- "$AREA_PATH" ':!documentation' | wc -c)"
      SCOPE="Changes since commit $BASE: run 'git diff $BASE..HEAD --stat -- $AREA_PATH :!documentation' and read only the relevant files. Update only the affected pages."
    elif [ "$FULL" -eq 1 ]; then
      BYTES="$(git -C "$ROOT" ls-files -z -- "$AREA_PATH" ':!documentation' | (cd "$ROOT" && xargs -0 -r cat) | wc -c)"
      SCOPE="First generation for this area: analyze '$AREA_PATH' fully."
    else
      BYTES=0 # MVP reads a bounded set of files
      SCOPE="MVP generation for this area: read only entrypoints, routes/menus and schemas (about 30 files at most), write the architecture overview and 2-3 representative pages, and list what is not covered yet under 'Not yet documented' in index.md. Do not read the whole area."
    fi
    TOK=$((BYTES / 4)); MAX="${DOCS_MAX_TOKENS:-50000}"
    if [ "$TOK" -gt "$MAX" ] && [ "$YES" -eq 0 ]; then
      echo ">> Area $AREA: ~$((TOK / 1000))k tokens to read (limit $((MAX / 1000))k, set DOCS_MAX_TOKENS)."
      if [ -t 0 ]; then read -r -p "   Continue? [y/N] " ANS; else ANS=n; fi
      [ "$ANS" = "y" ] || { echo "   Skipped $AREA (rerun with --yes to accept the cost)."; continue; }
    fi
    PROMPT="Follow the rules in $RULES and update documentation/source. Area: $AREA ($AREA_PATH). $SCOPE Edit only documentation/source/ and the nav of documentation/mkdocs.yml."
    echo ">> Documenting area: $AREA ($AREA_PATH)"
    if [ -z "${DOCS_LLM:-}" ]; then
      # Claude Code: tools restricted to documentation/source/
      (cd "$ROOT" && claude -p "$PROMPT" \
        --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Edit(documentation/source/**),Edit(documentation/mkdocs.yml),Write(documentation/source/**)")
    else
      # ponytail: word splitting on purpose (DOCS_LLM = command + flags); review git diff afterwards
      (cd "$ROOT" && $DOCS_LLM "$PROMPT")
    fi
    git -C "$ROOT" rev-parse HEAD > "$STATE"
  done
fi

# --- 2. HTML: MkDocs goes into a local venv the first time (system Python untouched) ---
PY="$(command -v python3 || command -v python || command -v py || true)"
[ -n "$PY" ] || { echo "ERROR: Python 3 not found."; exit 1; }
if [ ! -d "$DOC_DIR/.venv" ]; then "$PY" -m venv "$DOC_DIR/.venv"; fi
VPY="$DOC_DIR/.venv/Scripts/python"; [ -x "$VPY" ] || [ -f "$VPY.exe" ] || VPY="$DOC_DIR/.venv/bin/python"
"$VPY" -m pip install -q -r "$DOC_DIR/requirements.txt"
# Built from documentation/ so snippets (base_path "..") resolve from the repo root.
# Built into a temp dir and swapped in only on success: a failed build never empties html/.
# --strict (never with -q: -q hides the warnings strict counts): broken links, missing snippets or pages left out of nav fail the build.
rm -rf "$DOC_DIR/.html-new"
(cd "$DOC_DIR" && "$VPY" -m mkdocs build --strict -f mkdocs.yml -d .html-new)
rm -rf "$DOC_DIR/html"
# ponytail: retry because on Windows antivirus/indexers briefly lock freshly written files ("Permission denied")
for _ in 1 2 3 4 5; do mv "$DOC_DIR/.html-new" "$DOC_DIR/html" 2>/dev/null && break; sleep 1; done
[ -d "$DOC_DIR/html" ] || { echo "ERROR: could not move the new site into html/ (a file is locked: antivirus, Explorer or a browser). It is in documentation/.html-new; rerun --html-only."; exit 1; }

# enable the pre-push reminder (idempotent), never over hooks the repo already uses (husky, .git/hooks/*)
if [ -d "$ROOT/.githooks" ] && [ -z "$(git -C "$ROOT" config core.hooksPath || true)" ]; then
  HOOKS="$(git -C "$ROOT" rev-parse --absolute-git-dir)/hooks"
  if ls "$HOOKS" 2>/dev/null | grep -qv '\.sample$'; then
    echo "NOTE: kept the existing hooks in $HOOKS. To get the docs reminder, call .githooks/pre-push from your pre-push hook."
  else
    git -C "$ROOT" config core.hooksPath .githooks
  fi
fi

echo "OK. Open documentation/html/index.html and review 'git status documentation/' before committing."

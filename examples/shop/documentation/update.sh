#!/usr/bin/env bash
# SnapDoczilla: (1) an agent CLI updates documentation/source from the code that changed,
# (2) the HTML site in documentation/html is rebuilt.
#   ./documentation/update.sh               -> every area in areas.conf: agent + HTML
#   ./documentation/update.sh --<area>      -> one area only (e.g. --front)
#   ./documentation/update.sh --html-only   -> HTML only (after editing .md by hand; no agent)
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

AREAS="$ALL"; HTML_ONLY=0
for a in "$@"; do
  if [ "$a" = "--html-only" ]; then HTML_ONLY=1
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
    if [ -n "$BASE" ]; then
      SCOPE="Changes since commit $BASE: run 'git diff $BASE..HEAD --stat -- $AREA_PATH :!documentation' and read only the relevant files. Update only the affected pages."
    else
      SCOPE="First generation for this area: analyze '$AREA_PATH' fully."
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
rm -rf "$DOC_DIR/html" && mv "$DOC_DIR/.html-new" "$DOC_DIR/html"

# enable the pre-push reminder (idempotent)
[ -d "$ROOT/.githooks" ] && git -C "$ROOT" config core.hooksPath .githooks

echo "OK. Open documentation/html/index.html and review 'git status documentation/' before committing."

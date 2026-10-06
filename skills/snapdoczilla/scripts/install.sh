#!/usr/bin/env bash
# SnapDoczilla installer: sets up the offline documentation system in a repo.
# Usage: install.sh <repo-root> "<Project name>" [language: en|es|...]   (default: en)
# Never overwrites an existing documentation/mkdocs.yml or .githooks/pre-push.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${1:?Usage: install.sh <repo-root> \"<Project name>\" [en|es|...]}"
NAME="${2:?Missing project name}"
LANG_CODE="${3:-en}"
case "$LANG_CODE" in en) LANGUAGE="English" ;; es) LANGUAGE="Spanish (español)" ;; *) LANGUAGE="$LANG_CODE" ;; esac
DEST="$REPO/documentation"

git -C "$REPO" rev-parse --show-toplevel >/dev/null 2>&1 || { echo "ERROR: $REPO is not a git repository"; exit 1; }
[ -e "$DEST/mkdocs.yml" ] && { echo "ERROR: $DEST is already set up. Nothing was changed."; exit 1; }

mkdir -p "$DEST" "$REPO/.githooks"
cp -R "$SKILL_DIR/assets/documentation/." "$DEST/"
[ -e "$REPO/.githooks/pre-push" ] || cp "$SKILL_DIR/assets/githooks/pre-push" "$REPO/.githooks/pre-push"
chmod +x "$DEST/update.sh" "$REPO/.githooks/pre-push"

# project name and language into templates (sed without -i: portable across macOS/Linux/Git Bash)
for f in "$DEST/mkdocs.yml" "$DEST/source/index.md" "$DEST/AGENT-RULES.md"; do
  sed -e "s|{{PROJECT}}|$NAME|g" -e "s|{{LANG}}|$LANG_CODE|g" -e "s|{{LANGUAGE}}|$LANGUAGE|g" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

# "edit this page" button: derive the web URL from the git remote (GitHub/GitLab; others skipped)
REMOTE="$(git -C "$REPO" remote get-url origin 2>/dev/null || true)"
WEB="$(echo "$REMOTE" | sed -E -e 's#^git@([^:]+):#https://\1/#' -e 's#^(https?://)[^@/]+@#\1#' -e 's#\.git$##')"
BRANCH="$(git -C "$REPO" symbolic-ref --short HEAD 2>/dev/null || echo main)"
case "$WEB" in
  https://github.com/*) EDIT="edit/$BRANCH/documentation/source/" ;;
  https://gitlab.*|https://*gitlab*) EDIT="-/edit/$BRANCH/documentation/source/" ;;
  *) EDIT="" ;;
esac
[ -n "$EDIT" ] && printf '\nrepo_url: %s\nedit_uri: %s\n' "$WEB" "$EDIT" >> "$DEST/mkdocs.yml"

# the local venv and temp build dir are not versioned; the generated HTML is (read with zero setup)
GI="$REPO/.gitignore"
grep -qs '^documentation/.venv/' "$GI" || printf '\n# SnapDoczilla: local venv and temp build dir\ndocumentation/.venv/\ndocumentation/.html-new/\n' >> "$GI"

# scripts must keep LF line endings (with CRLF, bash fails on Linux/macOS/Git Bash)
GA="$REPO/.gitattributes"
grep -qs 'SnapDoczilla' "$GA" || printf '\n# SnapDoczilla\ndocumentation/*.sh text eol=lf\n.githooks/* text eol=lf\ndocumentation/source/assets/mermaid.min.js -text\n' >> "$GA"

# local Mermaid copy: diagrams render without internet (downloaded once)
MERMAID="$DEST/source/assets/mermaid.min.js"
if ! curl -fsSL -o "$MERMAID" "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"; then
  rm -f "$MERMAID"
  echo "WARNING: could not download Mermaid. Save https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js as $MERMAID"
fi

echo "SnapDoczilla installed in $DEST"

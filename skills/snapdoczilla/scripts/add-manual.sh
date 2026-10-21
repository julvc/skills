#!/usr/bin/env bash
# SnapDoczilla: adds an end-user manual (source/user-manual/) to an existing install, any profile.
# Usage: add-manual.sh <repo-root>
# Refuses if SnapDoczilla is not installed or the manual already exists.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${1:?Usage: add-manual.sh <repo-root>}"
DEST="$REPO/documentation"

[ -f "$DEST/mkdocs.yml" ] && [ -f "$DEST/update.sh" ] || { echo "ERROR: SnapDoczilla is not installed in $REPO"; exit 1; }
[ -e "$DEST/source/user-manual" ] && { echo "ERROR: $DEST/source/user-manual already exists. Nothing was changed."; exit 1; }

cp "$SKILL_DIR/assets/manual/AGENT-RULES-MANUAL.md" "$DEST/"
cp -R "$SKILL_DIR/assets/manual/source/user-manual" "$DEST/source/"
mkdir -p "$DEST/source/user-manual/img"

# every agent reads AGENT-RULES.md (update.sh, MCP get_rules): point it to the manual rules
printf '\n## User manual\n\nThis project has an end-user manual in `source/user-manual/`. Whenever a change affects what users see or do, also follow `documentation/AGENT-RULES-MANUAL.md`.\n' >> "$DEST/AGENT-RULES.md"

# nav: the section goes right after the last nav entry (repo_url/edit_uri may follow nav)
awk 'nav && /^[^ \t-]/ && !done { print "  - User manual:\n      - user-manual/index.md"; done=1 }
     { print }
     /^nav:/ { nav=1 }
     END { if (!done) print "  - User manual:\n      - user-manual/index.md" }' "$DEST/mkdocs.yml" > "$DEST/mkdocs.yml.tmp"
mv "$DEST/mkdocs.yml.tmp" "$DEST/mkdocs.yml"

echo "User manual added in $DEST/source/user-manual"

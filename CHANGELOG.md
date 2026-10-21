# Changelog

## 1.2.0

**New: user manual (flow D).** Writes an end-user manual from the real UI code, on any profile (`standard` or `cmmi`):
one step-by-step page per function with the exact button and field labels, the expected result and a
*Message → Cause → What to do* table built from the messages the app shows. Screenshots are left as placeholders
for a human to capture.

- Script: `bash skills/snapdoczilla/scripts/add-manual.sh <repo>`.
- MCP: new tool `snapdoczilla_add_manual`; `snapdoczilla_get_rules` also returns `AGENT-RULES-MANUAL.md`;
  `snapdoczilla_write_page` places pages next to their folder's entries in `nav:`.
- With the `cmmi` profile the manual is referenced as OT/VV evidence.

**Fixed**

- `update.sh` no longer overrides `core.hooksPath` or the hooks in `.git/hooks/` when the repo already has its own
  (it used to silently disable them). Without hooks it still enables `.githooks/pre-push`.
- `update.sh` retries the `html/` swap on Windows, where antivirus or indexers can briefly lock fresh files
  (`Permission denied`) and left `html/` empty.

**Upgrading**

- `pip install -U snapdoczilla-mcp` (or `uvx snapdoczilla-mcp@latest`) and update the plugin.
- Nothing changes in repos already documented: the manual is opt-in.
- Repos installed earlier keep their old `documentation/update.sh`. To get the two fixes above, copy the new
  `skills/snapdoczilla/assets/documentation/update.sh` over it.

## 1.1.0

**New: CMMI profile.** `install.sh <repo> "<Name>" <lang> cmmi` (MCP: `snapdoczilla_install` with `profile: "cmmi"`) adds a
*Process evidence* page that maps CMMI practice areas to repo evidence, a Requirement → Code → Tests → Page
traceability matrix, a baselines table per release tag and DAR-style ADR rules. The docs support an appraisal; they
never claim compliance.

## 1.0.0

Initial release: SnapDoczilla skill and MCP server (stdio).

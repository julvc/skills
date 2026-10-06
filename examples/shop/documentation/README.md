# Project documentation (SnapDoczilla)

- **Read:** open `documentation/html/index.html` with a double click. No install, no internet.
- **Update:** `documentation/update.cmd` (Windows) or `./documentation/update.sh`. Options: `--<area>` (see `areas.conf`) or `--html-only` (no agent). Review the changes and commit.
- Editable source: `documentation/source/*.md`. Rules for the agent: `documentation/AGENT-RULES*.md`.
- To update you need Git (with bash), Python 3 and an agent CLI: Claude Code by default, or another one via `DOCS_LLM` (e.g. `DOCS_LLM="codex exec --full-auto"`). No agent: `--html-only`.

Generated with [SnapDoczilla](https://github.com/julvc/skills).

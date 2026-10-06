# Rules for the agent that updates this documentation

- **Documentation language: English.** Write every page, heading and marker in this language. Technical, direct tone.
- **Edit only `documentation/source/`** (plus the `nav:` in `documentation/mkdocs.yml` when adding a page). Never touch code, `html/` or other folders.
- Document only what exists in the code. Anything you cannot verify gets a `> ⚠️` "to be confirmed" note (written in the documentation language). Never invent endpoints, tables or credentials (use `{PLACEHOLDER}`). Never copy secrets, tokens or passwords.
- Diagrams: ```` ```mermaid ```` blocks inside the `.md` files (they render offline).
- Real code in the docs: never paste it; embed it with `--8<-- "path/from/repo/root"` (see `AGENT-RULES-COMPONENTS.md`).
- Base pages (keep the file names; every new page also goes into `nav:`):
  - `index.md`: what the project is, stack and versions.
  - `getting-started.md`: requirements, how to run and test, taken from real files (README, build, config). If an existing README contradicts the real build, point out the discrepancy.
  - `architecture.md`: layers, integrations and main flows, with Mermaid.
  - `api.md`: only if the project exposes an API; read the real routes/controllers.
  - `adr/NNNN-title.md`: one decision per file (Context, Decision, Consequences). New ADRs only for real architecture decisions (new library, database change, new pattern).
- Incremental updates: change only the pages affected by the diff; don't rewrite what is still valid.
- Keep the last line of `index.md` as `Last sync: <short hash> (<date>)` (translated to the documentation language).
- Code areas and their paths live in `areas.conf`.
- The build runs with `--strict`: every page must be listed in `nav:`, and every link and snippet path must resolve. A failed build keeps the previous `html/`; fix the cause and rebuild.

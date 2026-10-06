---
name: snapdoczilla
description: SnapDoczilla - sets up and maintains technical documentation for any repository (any backend, any frontend) as a 100% offline HTML site that lives inside the repo - no Confluence, no servers, no CI. Readers double-click documentation/html/index.html; any dev refreshes it with one command. Built with MkDocs Material, local Mermaid diagrams and react.dev-style component pages that embed real source code and real usage. Use it whenever the user wants to document a project or codebase, set up "docs as code", generate or update architecture/API/ADR/onboarding docs, document frontend components, or asks to "document this project" / "documenta este proyecto" / "actualiza la documentación" - even if they don't name SnapDoczilla or MkDocs. Also use it when a repo already has documentation/update.sh and the user asks to update the docs.
---

# SnapDoczilla

Leaves a documentation system in the repo that **anyone reads with a double click** (no install, no internet) and **any dev updates with one command**.

`SKILL_DIR` below means the folder that contains this `SKILL.md`.

## Scope

**What it documents** — any stack, as long as the code is in the repo:

| Area | Pages produced | Source of truth |
|---|---|---|
| Any project | `index.md` (what it is, stack, versions), `getting-started.md` (requirements, run, test), `adr/0001-*.md` | build files, README, config |
| Backend | `architecture.md` (layers, integrations, main flows in Mermaid), `api.md` (endpoints grouped by resource), data model if there is one | routes/controllers, services, clients, migrations/schemas |
| Frontend | screen/route map, `src/` structure, state management, **component pages** (what it is, props/events/slots, real usage, real code) | router, views/pages, components, stores |

Where to look, by stack (not exhaustive — read whatever the repo actually uses):

| Stack | Endpoints / routes | Run & build |
|---|---|---|
| Spring / Java | `@RestController`, `@*Mapping`, `@HttpExchange`/Feign clients | `pom.xml`, `build.gradle`, `application.*` |
| Node (Express, Nest, Fastify) | `router.get(...)`, `@Controller`/`@Get` | `package.json` scripts |
| Python (FastAPI, Django, Flask) | `@app.get`, `urls.py`, `@bp.route` | `pyproject.toml`, `requirements*.txt`, `manage.py` |
| .NET | `[ApiController]`, `MapGet` | `*.csproj`, `appsettings*.json` |
| Go / PHP / Ruby | `http.HandleFunc`/router libs, `routes/*.php`, `config/routes.rb` | `go.mod`, `composer.json`, `Gemfile` |
| Vue / React / Angular / Svelte | `router/`, `app/` or `pages/` dirs, `*.routes.ts` | `package.json`, `vite.config.*`, `angular.json` |

**What it deliberately does not do:** screenshots or live demos (they force running the app and go stale on their own), hosting or publishing, replacing OpenAPI/Swagger (it links to it), inventing behavior the code doesn't show.

## Why it's designed this way

- **Everything inside the repo.** Docs travel with the code and are reviewed in the same PRs.
- **The HTML is committed.** Non-technical readers and new devs open `documentation/html/index.html`. The cost is big diffs in `html/`; accepted in exchange for zero setup.
- **Source code is never pasted.** Pages embed the real file at build time (`--8<-- "path"`), so they can't drift; if a file moves, the build fails naming it.
- **The agent assists, humans approve.** It writes the base and incremental updates; people review `git diff`. Anything it cannot verify is flagged as "to be confirmed".
- **Areas are independent.** `back`, `front`, etc. each have their own sync marker and command, so a frontend dev never regenerates backend docs.

## Pick a flow

| Situation | Flow |
|---|---|
| No `documentation/mkdocs.yml` yet and the user wants docs | **A. Install** |
| `documentation/` exists and they want it refreshed | **B. Update** |
| They want one component documented | **C. Component page** |

If the repo already has a `documentation/` folder that was **not** made by SnapDoczilla (no `mkdocs.yml` + `update.sh`), stop and ask before touching it.

## A. Install

1. **Check prerequisites** — report what's missing, never install anything global: `git` (must be a git repo), `python3`/`python`, `bash` (on Windows it ships with Git for Windows). An agent CLI (`claude`, `codex`, `opencode`…) is only needed for one-command updates later; `--html-only` works without it.
2. **Detect areas.** Look for `backend/`, `frontend/`, `api/`, `web/`, `apps/*`, `packages/*`, `src/`. One block → a single area `code=.`. Clearly separate parts → one area each (`back=backend/`, `front=frontend/`). Ask only if the split is not evident.
3. **Pick the docs language:** the language the user is writing in, unless they ask for another (`en`, `es`, …).
4. **Run the installer** (copies templates, downloads Mermaid once, adds `.gitignore`/`.gitattributes` lines; refuses to overwrite an existing install):
   ```bash
   bash "$SKILL_DIR/scripts/install.sh" "<repo-root>" "<Project name>" <lang>
   ```
5. **Write `documentation/areas.conf`** with the detected areas (`name=path`).
6. **UI areas:** copy `documentation/AGENT-RULES-COMPONENTS.md` to `documentation/AGENT-RULES-<area>.md` (e.g. `AGENT-RULES-front.md`); per-area rules are picked up automatically. No UI area → delete the template.
7. **Generate the first content** in `documentation/source/`, following `AGENT-RULES.md` (and each area's rules) and the Scope table above. For UI areas, write 2–3 component pages for representative components (ask which, or pick the most reused). Read real code; don't invent. Add every page to `nav:` in `mkdocs.yml`.
8. **Existing docs** (md, docx, pdf) are context for the *why*, never a substitute for reading code. Convert docx/pdf to Markdown before reading, and never copy secrets or tokens they may contain.
9. **Mark sync:** for each area, `git rev-parse HEAD > documentation/.last-sync-<area>`.
10. **Build and verify:**
    ```bash
    bash documentation/update.sh --html-only
    ```
    First build installs MkDocs into `documentation/.venv` (1–2 min, needs internet). `snippet ... could not be found` → fix that path. If Chrome/Edge is available, open `html/architecture.html` headless with `--allow-file-access-from-files --dump-dom` and check there are more `<svg` than on a page without diagrams (Material adds ~7 icons).
11. **Hand over** a short summary: what was created, how to read it, how to update it (below), what is flagged as to be confirmed. **Do not commit or push** — that is the user's call.

## B. Update

- **From a terminal:** `documentation/update.cmd` (Windows double-click) or `./documentation/update.sh [--<area>] [--html-only]`. It sends the diff since `.last-sync-<area>` to an agent CLI, which edits only `source/`, then rebuilds the HTML (atomically: a failed build never empties `html/`). Default CLI is Claude Code with tools restricted to `documentation/source/`; set `DOCS_LLM` to use another agent:

  | Agent | `DOCS_LLM` |
  |---|---|
  | Claude Code | *(unset — default)* |
  | Codex CLI | `codex exec --full-auto` |
  | OpenCode | `opencode run` |
  | Gemini CLI | `gemini --yolo -p` |
  | Other | any non-interactive command that takes the prompt as its last argument |

  Only the Claude default restricts writable paths; with other agents rely on their sandbox and review `git diff`.
- **Inside this session (any agent, incl. Antigravity):** read `AGENT-RULES*.md`, run `git diff <hash in .last-sync-<area>>..HEAD -- <area path>`, edit only the affected pages, run `bash documentation/update.sh --html-only`, then `git rev-parse HEAD > documentation/.last-sync-<area>`.
- Check line-range snippets (`path:START:END`) when their source file changed: they don't fail when they drift, they just show the wrong lines.

## C. Component page

Follow `AGENT-RULES-COMPONENTS.md`: what it is → how it works → API → **real usage example** → **real source code** → things to know. Read the component *and* its real consumers; the usage example comes from an existing screen (if none exists, label it as illustrative). Incomplete component (empty files, `console.log`, commented-out code) → say so in a `!!! warning` block. Add the page to `nav:`.

## Good to know

- Diagrams are ```` ```mermaid ```` blocks. The fence class is `diagram` on purpose: it stops Material from loading Mermaid from the internet; `assets/diagrams.js` renders them with the local copy.
- Builds are `--strict` with `validation` set to `warn`: a page missing from `nav:`, a broken link or a missing snippet fails the build (and the previous `html/` stays). Fix the cause; never loosen the config to get a green build.
- `install.sh` sets `repo_url`/`edit_uri` from the `origin` remote (GitHub/GitLab) so every page gets an "edit this page" button; other hosts are skipped silently.
- Readers get a light/dark toggle; diagrams redraw in the matching theme.
- The user wants it on the web too? `html/` is a static site: point them to the GitHub Pages workflow in the SnapDoczilla README instead of adding hosting yourself.
- `requirements.txt` pins `mkdocs<2` and `mkdocs-material<10` (MkDocs 2.0 breaks plugins).
- First run needs internet (pip + one Mermaid download); reading never does.
- Merge conflict in `html/`: resolve the `.md` files, rerun `--html-only`, commit the result. Never hand-merge HTML.
- Suggest naming **one docs owner** who reviews, while any dev can run the update.

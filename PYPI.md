# SnapDoczilla MCP server

<!-- mcp-name: io.github.julvc/snapdoczilla -->

Offline **docs-as-code** for any backend and any frontend, driven by your AI agent. SnapDoczilla keeps a
`documentation/` folder inside your repo: a static HTML site (MkDocs Material, local Mermaid diagrams, ADRs,
API map and component pages with **real code and real usage**) that anyone opens with a double click and any dev
refreshes with one command.

This MCP server gives your agent the deterministic half of that workflow. **The agent writes the docs from your
code; the server installs, tracks what changed since the last documented commit, writes pages safely, and builds the site.**

## Install

Needs `uv` (for `uvx`), `git`, and `bash` (on Windows: [Git for Windows](https://git-scm.com)). Building the site
also needs Python 3 on `PATH`, and internet the first time (MkDocs and Mermaid are downloaded once).

**Claude Code**

```bash
claude mcp add snapdoczilla -- uvx snapdoczilla-mcp
```

**Claude Desktop, Cursor and other clients that use `mcpServers` JSON**

```json
{
  "mcpServers": {
    "snapdoczilla": {
      "command": "uvx",
      "args": ["snapdoczilla-mcp"]
    }
  }
}
```

**Codex CLI** (`~/.codex/config.toml`)

```toml
[mcp_servers.snapdoczilla]
command = "uvx"
args = ["snapdoczilla-mcp"]
```

This server does **not** read your source code. Your client does, with its own file tools (Claude Code, Cursor and
Codex have them; in Claude Desktop add a filesystem server).

## Tools

| Tool | What it does |
|---|---|
| `snapdoczilla_status` | Installed? Areas, commits not yet documented per area, existing pages, next ADR number, suggested next step. Start here. |
| `snapdoczilla_install` | Scaffolds `documentation/` (templates, update script, pre-push reminder), writes `areas.conf`, downloads Mermaid once. Refuses to touch a `documentation/` it did not create. |
| `snapdoczilla_get_rules` | Returns the rules the pages must follow (language, never invent, embed real code). |
| `snapdoczilla_changes_since_sync` | Files, commits and diffstat of an area since its last documented commit, so only affected pages are updated. |
| `snapdoczilla_write_page` | Creates or overwrites one Markdown page, confined to `documentation/source/`, and adds it to `nav`. |
| `snapdoczilla_build_html` | Strict MkDocs build into `documentation/html/`. A failed build keeps the previous site. No AI agent is invoked. |
| `snapdoczilla_mark_synced` | Records HEAD as the last documented commit of an area. |

There is also a prompt, `document_project`, that starts the whole flow.

## Typical use

Ask your agent: *"Document this project"* (or *"update the docs"*). It checks status, installs if needed, reads the
real code, writes the pages, builds, and marks the areas as synced. It never commits or pushes: you review `git diff`.

## Also available as a plain Agent Skill

The same workflow ships as a [`SKILL.md`](https://github.com/julvc/skills/blob/main/skills/snapdoczilla/SKILL.md)
for Claude Code, Codex, OpenCode, Gemini CLI and more. See the
[repository](https://github.com/julvc/skills) for screenshots, the `examples/shop` result and the full documentation.

MIT License.

"""SnapDoczilla MCP server (stdio). Run with ``snapdoczilla-mcp`` or ``uvx snapdoczilla-mcp``."""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__, core

INSTRUCTIONS = """\
SnapDoczilla keeps offline docs-as-code (MkDocs Material + local Mermaid) inside a git repo.
YOU write the documentation from the real code; these tools do the deterministic parts.
This server does not read source code: use your client's own file tools for that.

Workflow
1. snapdoczilla_status(repo): installed? which areas are out of date?
2. Not installed: snapdoczilla_install (choose areas from the repo layout), then write the base pages.
3. Installed: snapdoczilla_changes_since_sync(area), read ONLY the changed code, update ONLY the affected pages.
4. snapdoczilla_get_rules before writing, and follow it (language, never invent, embed real code).
5. snapdoczilla_write_page writes inside documentation/source/ only and can add the page to nav.
6. snapdoczilla_build_html is strict: fix every reported problem, never loosen the config.
7. snapdoczilla_mark_synced once an area is documented up to HEAD.
Never commit or push. Anything you cannot verify in the code is flagged as "to be confirmed".
"""

mcp = MCPServer("snapdoczilla", instructions=INSTRUCTIONS, version=__version__)

Repo = Annotated[str, Field(description="Absolute path of the git repository (any folder inside it works).")]
Area = Annotated[str, Field(description="Area name from documentation/areas.conf, e.g. 'back' or 'front'.")]

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
WRITES_DOCS = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)


async def _off_loop(fn, *args) -> dict[str, Any]:
    """Blocking work (git, bash, mkdocs) runs in a thread so the protocol loop keeps answering."""
    try:
        return await asyncio.to_thread(fn, *args)
    except core.SnapDoczillaError as exc:
        raise ToolError(str(exc)) from None  # expected problems: show the model the real message


@mcp.tool(name="snapdoczilla_status", annotations=READ_ONLY)
async def snapdoczilla_status(repo: Repo) -> dict[str, Any]:
    """Report whether SnapDoczilla is installed in the repo, its areas, how many commits each area is
    behind its docs, the existing pages, the next ADR number and the suggested next step. Call this first."""
    return await _off_loop(core.status, repo)


@mcp.tool(name="snapdoczilla_install",
          annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True))
async def snapdoczilla_install(
    repo: Repo,
    project_name: Annotated[str, Field(description="Human name shown as the site title.")],
    language: Annotated[str, Field(description="Docs language code: 'en', 'es', ...")] = "en",
    areas: Annotated[dict[str, str] | None, Field(
        description="Code areas as {name: path relative to the repo root}, e.g. {'back': 'backend/', 'front': 'frontend/'}. "
                    "Omit for a single area covering the whole repo.")] = None,
    ui_areas: Annotated[list[str] | None, Field(
        description="Names from `areas` that contain UI components; they get component-page rules.")] = None,
) -> dict[str, Any]:
    """Install the documentation scaffold into documentation/ (templates, update script, pre-push reminder)
    and download Mermaid once (needs internet). Refuses to touch an existing documentation/ folder."""
    return await _off_loop(core.install, repo, project_name, language, areas, ui_areas)


@mcp.tool(name="snapdoczilla_get_rules", annotations=READ_ONLY)
async def snapdoczilla_get_rules(repo: Repo, area: Annotated[str | None, Field(
        description="Also return this area's AGENT-RULES-<area>.md when it exists.")] = None) -> dict[str, Any]:
    """Return the rules the documentation must follow (language, tone, page layout, no invention)."""
    return await _off_loop(core.get_rules, repo, area)


@mcp.tool(name="snapdoczilla_changes_since_sync", annotations=READ_ONLY)
async def snapdoczilla_changes_since_sync(repo: Repo, area: Area) -> dict[str, Any]:
    """List the files, commits and diffstat of an area since its last documented commit, so only the
    affected pages are updated. With no previous sync it says to analyze the whole area."""
    return await _off_loop(core.changes_since_sync, repo, area)


@mcp.tool(name="snapdoczilla_write_page", annotations=WRITES_DOCS)
async def snapdoczilla_write_page(
    repo: Repo,
    page: Annotated[str, Field(description="Path inside documentation/source/, e.g. 'architecture.md' or 'adr/0002-use-queue.md'.")],
    content: Annotated[str, Field(description="Full Markdown of the page. Embed real code with --8<-- \"path/from/repo/root\".")],
    nav_title: Annotated[str | None, Field(
        description="Menu title. Pass it when creating a page so it is added to nav (the strict build needs that).")] = None,
) -> dict[str, Any]:
    """Create or overwrite one Markdown page. Writes are confined to documentation/source/."""
    return await _off_loop(core.write_page, repo, page, content, nav_title)


@mcp.tool(name="snapdoczilla_build_html", annotations=WRITES_DOCS)
async def snapdoczilla_build_html(repo: Repo) -> dict[str, Any]:
    """Rebuild documentation/html with a strict MkDocs build (no AI agent is invoked). The first run creates a
    local venv and installs MkDocs, which takes a minute or two and needs internet. A failed build keeps the old html."""
    return await _off_loop(core.build_html, repo)


@mcp.tool(name="snapdoczilla_mark_synced", annotations=WRITES_DOCS)
async def snapdoczilla_mark_synced(repo: Repo, area: Area) -> dict[str, Any]:
    """Record the current HEAD as the last documented commit of an area. Call it after the area's pages are updated."""
    return await _off_loop(core.mark_synced, repo, area)


@mcp.prompt(name="document_project", title="Document this project with SnapDoczilla")
def document_project(language: str = "en") -> str:
    return (
        f"Document this repository with SnapDoczilla in {language}. Start with snapdoczilla_status. "
        "Install if needed, write the base pages from the real code (read it with your file tools), "
        "build the HTML, fix every reported problem, mark each area as synced, then summarize what "
        "was created and what is flagged as to be confirmed. Do not commit or push."
    )


def main() -> None:
    if "--version" in sys.argv[1:]:
        print(__version__)
        return
    mcp.run()  # stdio; stdout is reserved for the protocol


if __name__ == "__main__":
    main()

"""Smoke test for the SnapDoczilla MCP server, over real stdio.

    python tests/mcp_smoke.py                       # everything except the real MkDocs build (stubbed)
    SNAPDOCZILLA_TEST_BUILD=1 python tests/mcp_smoke.py   # also runs the real strict build (needs internet)
    SNAPDOCZILLA_USE_INSTALLED=1 python tests/mcp_smoke.py  # test the pip-installed package instead of ./src

Needs: git, bash, curl, and the `mcp` package. Works from a checkout (no install needed).
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

ROOT = Path(__file__).resolve().parent.parent
REAL_BUILD = os.environ.get("SNAPDOCZILLA_TEST_BUILD") == "1"
STUB_UPDATE = """#!/usr/bin/env bash
[ "$1" = "--html-only" ] || { echo "unexpected args: $*"; exit 2; }
mkdir -p "$(dirname "$0")/html" && echo ok > "$(dirname "$0")/html/index.html"
echo "OK (stub build)"
"""


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


async def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="snapdoc-mcp-"))
    repo = tmp / "shop"
    (repo / "backend").mkdir(parents=True)
    (repo / "frontend").mkdir()
    (repo / "backend" / "app.py").write_text("def hello():\n    return 'hi'\n")
    (repo / "frontend" / "Button.jsx").write_text("export const Button = () => null;\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    git(repo, "config", "user.email", "smoke@test")
    git(repo, "config", "user.name", "smoke")
    git(repo, "remote", "add", "origin", "git@github.com:acme/shop.git")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")

    params = StdioServerParameters(
        command=sys.executable, args=["-m", "snapdoczilla_mcp.server"],
        env=os.environ.copy() if os.environ.get("SNAPDOCZILLA_USE_INSTALLED") else {**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    async with Client(params) as c:
        async def call(name: str, args: dict, ok: bool = True) -> dict:
            r = await c.call_tool(name, args)
            if r.is_error == ok:
                fail(f"{name} {args} -> is_error={r.is_error}: {r.content[0].text if r.content else ''}")
            return r.structured_content if ok else {"error": r.content[0].text}

        print("1. tools and prompt are exposed")
        names = {t.name for t in (await c.list_tools()).tools}
        expected = {"snapdoczilla_" + n for n in
                    ("status", "install", "get_rules", "changes_since_sync", "write_page", "build_html", "mark_synced")}
        if names != expected:
            fail(f"tools differ: {sorted(names ^ expected)}")
        if "document_project" not in {p.name for p in (await c.list_prompts()).prompts}:
            fail("prompt document_project missing")

        print("2. status before install")
        s = await call("snapdoczilla_status", {"repo": str(repo / "backend")})  # a subfolder resolves to the repo root
        if s["installed"] or s["foreign_documentation_dir"]:
            fail(f"unexpected status: {s}")

        print("3. install with areas; bad input is rejected")
        err = await call("snapdoczilla_install", {"repo": str(repo), "project_name": 'Bad "name"'}, ok=False)
        err = await call("snapdoczilla_install", {"repo": str(repo), "project_name": "Shop", "areas": {"x": "../etc"}}, ok=False)
        if (repo / "documentation").exists():
            fail("a rejected install must not create documentation/")
        r = await call("snapdoczilla_install", {
            "repo": str(repo), "project_name": "R&D | Shop", "language": "en",
            "areas": {"back": "backend/", "front": "frontend/"}, "ui_areas": ["front"],
        })
        doc = repo / "documentation"
        conf = (doc / "areas.conf").read_text()
        if "back=backend/" not in conf or "front=frontend/" not in conf or "code=." in conf:
            fail(f"areas.conf wrong:\n{conf}")
        if not (doc / "AGENT-RULES-front.md").is_file() or (doc / "AGENT-RULES-back.md").exists():
            fail("component rules must exist only for the UI area")
        if "R&D | Shop" not in (doc / "mkdocs.yml").read_text():
            fail("project name with & and | was not preserved")
        await call("snapdoczilla_install", {"repo": str(repo), "project_name": "Again"}, ok=False)

        print("4. rules")
        rules = (await call("snapdoczilla_get_rules", {"repo": str(repo), "area": "front"}))["rules"]
        if set(rules) != {"AGENT-RULES.md", "AGENT-RULES-front.md"}:
            fail(f"rules files: {list(rules)}")

        print("5. write_page: confined to source/, adds to nav once")
        for bad in ("../x.md", "/abs.md", "assets/x.md", ".hidden.md", "a/../../b.md", "page.txt"):
            await call("snapdoczilla_write_page", {"repo": str(repo), "page": bad, "content": "x"}, ok=False)
        w = await call("snapdoczilla_write_page", {
            "repo": str(repo), "page": "adr/0001-use-queue.md", "content": "# ADR\n", "nav_title": "ADR 1: queue"})
        if not (w["created"] and w["nav_added"]):
            fail(f"first write: {w}")
        w = await call("snapdoczilla_write_page", {
            "repo": str(repo), "page": "adr/0001-use-queue.md", "content": "# ADR v2\n", "nav_title": "ADR 1: queue"})
        if w["created"] or w["nav_added"]:
            fail(f"second write must not duplicate nav: {w}")
        nav = (doc / "mkdocs.yml").read_text()
        if nav.count("adr/0001-use-queue.md") != 1 or '- "ADR 1: queue": adr/0001-use-queue.md' not in nav:
            fail(f"nav entry wrong:\n{nav}")
        st = await call("snapdoczilla_status", {"repo": str(repo)})
        if st["next_adr_number"] != "0002" or "adr/0001-use-queue.md" not in st["pages"]:
            fail(f"status after write: {st}")

        print("6. sync markers and changes")
        ch = await call("snapdoczilla_changes_since_sync", {"repo": str(repo), "area": "back"})
        if not ch["first_generation"]:
            fail("no marker must mean first generation")
        await call("snapdoczilla_mark_synced", {"repo": str(repo), "area": "back"})
        await call("snapdoczilla_mark_synced", {"repo": str(repo), "area": "nope"}, ok=False)
        if (doc / ".last-sync-back").read_text().strip() != git(repo, "rev-parse", "HEAD"):
            fail("marker is not HEAD")
        (repo / "backend" / "app.py").write_text("def hello():\n    return 'hello'\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "change backend")
        ch = await call("snapdoczilla_changes_since_sync", {"repo": str(repo), "area": "back"})
        if ch["first_generation"] or not any("backend/app.py" in f for f in ch["changed_files"]):
            fail(f"changes: {ch}")
        st = await call("snapdoczilla_status", {"repo": str(repo)})
        by = {a["name"]: a for a in st["areas"]}
        if by["back"]["commits_not_documented"] != 1 or by["front"]["last_sync"] is not None:
            fail(f"status areas: {by}")

        print("7. build_html" + (" (REAL strict build)" if REAL_BUILD else " (stubbed MkDocs)"))
        if not REAL_BUILD:
            (doc / "update.sh").write_text(STUB_UPDATE)
        else:
            (doc / "source" / "index.md").write_text("# Shop\n\n```mermaid\nflowchart LR\n  a --> b\n```\n")
        b = await call("snapdoczilla_build_html", {"repo": str(repo)})
        if not b["ok"] or not (doc / "html" / "index.html").is_file():
            fail(f"build: {b}")
        if REAL_BUILD:
            (doc / "source" / "orphan.md").write_text("# not in nav\n")
            b = await call("snapdoczilla_build_html", {"repo": str(repo)})
            if b["ok"]:
                fail("a page outside nav must fail the strict build")
            (doc / "source" / "orphan.md").unlink()

        print("8. a plain folder is not a repo")
        await call("snapdoczilla_status", {"repo": str(tmp)}, ok=False)

    print("All MCP smoke checks passed")


if __name__ == "__main__":
    asyncio.run(main())

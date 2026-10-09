"""Deterministic helpers behind the SnapDoczilla MCP tools (no MCP imports here).

The model writes the documentation. This module does the parts that must not
depend on a model: locating the repo, running the bundled installer and the
strict HTML build, tracking the last documented commit per area, and keeping
every write inside ``documentation/source/``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

MAX_OUTPUT = 4000
MAX_PAGE_BYTES = 1_000_000
HASH_RE = re.compile(r"^[0-9a-f]{7,64}$")
LANG_RE = re.compile(r"^[A-Za-z]{2,3}([_-][A-Za-z0-9]{2,8})?$")
AREA_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PAGE_RE = re.compile(r"^[\w.-]+(/[\w.-]+)*\.md$")


class SnapDoczillaError(Exception):
    """A problem the model can read and act on."""


# --------------------------------------------------------------------------- #
# Locating things
# --------------------------------------------------------------------------- #

def skill_dir() -> Path:
    """Folder with scripts/ and assets/: bundled in the wheel, or the repo checkout in dev."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "skill", here.parents[1] / "skills" / "snapdoczilla"):
        if (candidate / "scripts" / "install.sh").is_file():
            return candidate
    raise SnapDoczillaError("The bundled SnapDoczilla skill files are missing; reinstall snapdoczilla-mcp.")


def bash_exe() -> str:
    """bash for the bundled .sh scripts. On Windows only Git for Windows' bash (never WSL's)."""
    if os.name == "nt":
        roots = [os.environ.get(v) for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA")]
        candidates = [Path(r) / sub / "bin" / "bash.exe" for r in roots if r for sub in ("Git", "Programs/Git")]
        git = shutil.which("git")
        if git:
            candidates.append(Path(git).resolve().parent.parent / "bin" / "bash.exe")
        for c in candidates:
            if c.is_file():
                return str(c)
        raise SnapDoczillaError("Git for Windows (which ships bash) was not found. Install it from https://git-scm.com.")
    found = shutil.which("bash")
    if not found:
        raise SnapDoczillaError("bash was not found on PATH.")
    return found


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 60) -> tuple[int, str]:
    """Run a command with stdin closed: stdin belongs to the MCP protocol, children must not read it."""
    extra: dict[str, Any] = {}
    if os.name == "nt":
        extra["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    try:
        p = subprocess.run(
            cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, **extra,
        )
    except FileNotFoundError:
        raise SnapDoczillaError(f"Command not found: {cmd[0]}") from None
    except subprocess.TimeoutExpired:
        raise SnapDoczillaError(f"Timed out after {timeout}s: {' '.join(cmd[:3])} ...") from None
    return p.returncode, p.stdout


def _git(repo: Path, *args: str, timeout: int = 60) -> tuple[int, str]:
    return _run(["git", "-C", str(repo), *args], timeout=timeout)


def _tail(text: str, limit: int = MAX_OUTPUT) -> str:
    text = text.strip()
    return text if len(text) <= limit else "...[truncated]...\n" + text[-limit:]


def resolve_repo(path: str) -> Path:
    if not path or not str(path).strip():
        raise SnapDoczillaError("repo is required: the path of a git repository.")
    p = Path(str(path).strip()).expanduser()
    if not p.is_dir():
        raise SnapDoczillaError(f"Not a directory: {p}")
    rc, out = _git(p, "rev-parse", "--show-toplevel")
    if rc != 0:
        raise SnapDoczillaError(f"{p} is not inside a git repository.")
    return Path(out.strip())


def _doc(repo: Path) -> Path:
    return repo / "documentation"


def _installed(repo: Path) -> bool:
    d = _doc(repo)
    return (d / "mkdocs.yml").is_file() and (d / "update.sh").is_file()


def _require_installed(repo: Path) -> Path:
    if not _installed(repo):
        raise SnapDoczillaError("SnapDoczilla is not installed in this repo. Call snapdoczilla_install first.")
    return _doc(repo)


def read_areas(doc: Path) -> list[tuple[str, str]]:
    conf = doc / "areas.conf"
    if not conf.is_file():
        raise SnapDoczillaError("documentation/areas.conf is missing.")
    areas = []
    for line in conf.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            name, path = s.split("=", 1)
            areas.append((name.strip(), path.strip()))
    return areas


def _area_path(doc: Path, area: str) -> str:
    areas = dict(read_areas(doc))
    if area not in areas:
        raise SnapDoczillaError(f"Unknown area '{area}'. Areas in areas.conf: {', '.join(areas) or '(none)'}")
    return areas[area]


def _last_sync(doc: Path, area: str) -> str | None:
    marker = doc / f".last-sync-{area}"
    if not marker.is_file():
        return None
    value = marker.read_text(encoding="utf-8").strip()
    return value if HASH_RE.match(value) else None


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #

def status(repo_path: str) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _doc(repo)
    installed = _installed(repo)
    _, head = _git(repo, "rev-parse", "--short", "HEAD")
    result: dict[str, Any] = {
        "repo": str(repo),
        "head": head.strip() or None,
        "installed": installed,
        "foreign_documentation_dir": doc.exists() and not installed,
    }
    if result["foreign_documentation_dir"]:
        result["next_step"] = (
            "documentation/ exists but was not created by SnapDoczilla. Stop and ask the user before touching it."
        )
        return result
    if not installed:
        result["next_step"] = "Call snapdoczilla_install (choose the areas from the repo layout), then write the base pages."
        return result

    areas = []
    for name, path in read_areas(doc):
        last = _last_sync(doc, name)
        behind = None
        if last:
            rc, out = _git(repo, "rev-list", "--count", f"{last}..HEAD", "--", path, ":!documentation")
            behind = int(out.strip()) if rc == 0 and out.strip().isdigit() else None
        areas.append({
            "name": name, "path": path, "last_sync": last, "commits_not_documented": behind,
            "has_area_rules": (doc / f"AGENT-RULES-{name}.md").is_file(),
        })
    src = doc / "source"
    pages = sorted(p.relative_to(src).as_posix() for p in src.rglob("*.md")) if src.is_dir() else []
    adr_numbers = [int(m.group(1)) for p in pages if (m := re.match(r"adr/(\d{4})-", p))]
    result.update({
        "areas": areas,
        "pages": pages,
        "next_adr_number": f"{max(adr_numbers, default=0) + 1:04d}",
        "html_built": (doc / "html" / "index.html").is_file(),
    })
    stale = [a["name"] for a in areas if a["commits_not_documented"]]
    never = [a["name"] for a in areas if a["last_sync"] is None]
    if never:
        result["next_step"] = f"Areas never documented: {', '.join(never)}. Write their pages, build, then mark_synced."
    elif stale:
        result["next_step"] = f"Out of date: {', '.join(stale)}. Call snapdoczilla_changes_since_sync for each."
    else:
        result["next_step"] = "Everything is documented up to HEAD."
    return result


def install(repo_path: str, project_name: str, language: str = "en",
            areas: dict[str, str] | None = None, ui_areas: list[str] | None = None,
            profile: str = "standard") -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    name = (project_name or "").strip()
    if not name or any(ord(c) < 32 for c in name) or '"' in name:
        raise SnapDoczillaError('project_name must be non-empty, single-line, and contain no double quotes.')
    if not LANG_RE.match(language or ""):
        raise SnapDoczillaError("language must be a code such as 'en' or 'es'.")
    if profile not in ("standard", "cmmi"):
        raise SnapDoczillaError("profile must be 'standard' or 'cmmi'.")
    if _installed(repo):
        raise SnapDoczillaError("SnapDoczilla is already installed here. Nothing was changed.")
    if _doc(repo).exists():
        raise SnapDoczillaError("documentation/ already exists and was not created by SnapDoczilla. Ask the user first.")

    clean_areas = _validate_areas(repo, areas) if areas else None
    ui = list(ui_areas or [])
    if clean_areas is not None:
        unknown = [a for a in ui if a not in clean_areas]
        if unknown:
            raise SnapDoczillaError(f"ui_areas not in areas: {', '.join(unknown)}")
    elif ui:
        raise SnapDoczillaError("ui_areas requires areas.")

    # install.sh substitutes the name through sed with '|' as delimiter: escape sed's specials.
    sed_safe = name.replace("\\", "\\\\").replace("&", "\\&").replace("|", "\\|")
    script = (skill_dir() / "scripts" / "install.sh").as_posix()
    rc, out = _run([bash_exe(), script, repo.as_posix(), sed_safe, language, profile], timeout=180)
    if rc != 0:
        raise SnapDoczillaError(f"install.sh failed (exit {rc}):\n{_tail(out)}")

    doc = _doc(repo)
    notes: list[str] = []
    if "WARNING" in out:
        notes.append(next((l for l in out.splitlines() if "WARNING" in l), "Mermaid could not be downloaded."))
    if clean_areas is not None:
        header = [l for l in (doc / "areas.conf").read_text(encoding="utf-8").splitlines() if l.strip().startswith("#")]
        lines = header + [f"{n}={p}" for n, p in clean_areas.items()]
        (doc / "areas.conf").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        template = doc / "AGENT-RULES-COMPONENTS.md"
        for a in ui:
            shutil.copyfile(template, doc / f"AGENT-RULES-{a}.md")
        if not ui and template.is_file():
            template.unlink()
        notes.append(f"areas.conf written with: {', '.join(clean_areas)}")
    else:
        notes.append("areas.conf still has the default area code=.; edit it if the repo has separate back/front parts.")
    return {
        "installed": True,
        "documentation_dir": str(doc),
        "notes": notes,
        "next_step": "Call snapdoczilla_get_rules, write the base pages with snapdoczilla_write_page "
                     "(index, getting-started, architecture, api if any), then snapdoczilla_build_html and snapdoczilla_mark_synced.",
    }


def _validate_areas(repo: Path, areas: dict[str, str]) -> dict[str, str]:
    clean: dict[str, str] = {}
    for name, path in areas.items():
        if not AREA_RE.match(name):
            raise SnapDoczillaError(f"Invalid area name '{name}': use letters, digits, '-' or '_'.")
        p = path.strip().replace("\\", "/")
        if not p or p.startswith("/") or re.match(r"^[A-Za-z]:", p) or ".." in p.split("/") or "=" in p or "\n" in p:
            raise SnapDoczillaError(f"Invalid path for area '{name}': must be relative to the repo root.")
        if not (repo / p).is_dir():
            raise SnapDoczillaError(f"Path for area '{name}' is not a directory in the repo: {p}")
        clean[name] = p
    return clean


def get_rules(repo_path: str, area: str | None = None) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _require_installed(repo)
    names = ["AGENT-RULES.md"]
    if area:
        _area_path(doc, area)
        extra = f"AGENT-RULES-{area}.md"
        if (doc / extra).is_file():
            names.append(extra)
    return {"rules": {n: (doc / n).read_text(encoding="utf-8") for n in names if (doc / n).is_file()}}


def changes_since_sync(repo_path: str, area: str) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _require_installed(repo)
    path = _area_path(doc, area)
    last = _last_sync(doc, area)
    base: dict[str, Any] = {"area": area, "area_path": path, "last_sync": last}
    if last is None:
        return {**base, "first_generation": True,
                "hint": f"No sync marker: analyze '{path}' fully, then mark_synced."}
    rc, _ = _git(repo, "cat-file", "-e", f"{last}^{{commit}}")
    if rc != 0:
        return {**base, "first_generation": True,
                "hint": "The recorded commit no longer exists (history rewritten). Treat as a full pass."}
    spec = [f"{last}..HEAD", "--", path, ":!documentation"]
    _, names = _git(repo, "diff", "--name-status", *spec)
    _, stat = _git(repo, "diff", "--stat", *spec)
    _, log = _git(repo, "log", "--oneline", "-n", "30", *spec)
    files = names.strip().splitlines()
    return {
        **base, "first_generation": False,
        "changed_files": files[:200], "changed_files_truncated": len(files) > 200,
        "summary": _tail(stat, 1500), "commits": log.strip().splitlines(),
        "hint": "Read only these files, update only the affected pages. Only committed changes are listed.",
    }


def write_page(repo_path: str, page: str, content: str, nav_title: str | None = None) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _require_installed(repo)
    parts = page.split("/")
    if (not PAGE_RE.match(page) or any(p.startswith(".") for p in parts) or parts[0] == "assets"):
        raise SnapDoczillaError("page must be a relative .md path such as 'architecture.md' or 'adr/0002-use-queue.md'.")
    if "\x00" in content or len(content.encode("utf-8")) > MAX_PAGE_BYTES:
        raise SnapDoczillaError("content must not contain NUL characters and must be under 1 MB.")
    src = (doc / "source").resolve()
    target = (src / page).resolve()
    if not target.is_relative_to(src):
        raise SnapDoczillaError("page escapes documentation/source/.")
    created = not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    nav_added = False
    if nav_title:
        nav_added = _add_to_nav(doc / "mkdocs.yml", page, nav_title)
    return {
        "page": page, "created": created, "nav_added": nav_added,
        "reminder": "Every page must be in nav: or the strict build fails." if created and not nav_added else None,
    }


def _add_to_nav(mkdocs: Path, page: str, title: str) -> bool:
    if "\n" in title or "\r" in title:
        raise SnapDoczillaError("nav_title must be a single line.")
    raw = mkdocs.read_bytes().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    start = next((i for i, l in enumerate(lines) if l.rstrip() == "nav:"), None)
    if start is None:
        raise SnapDoczillaError("No top-level 'nav:' in documentation/mkdocs.yml; add the entry by hand.")
    last, j = start, start + 1
    while j < len(lines):
        l = lines[j]
        if l.strip() == "":
            j += 1
        elif l[0] in " \t-":
            if page in re.split(r"[\s:'\"]+", l):
                return False
            last, j = j, j + 1
        else:
            break
    indent = re.match(r"\s*", lines[start + 1]).group(0) if start + 1 < len(lines) and lines[start + 1].strip() else "  "
    lines.insert(last + 1, f"{indent or '  '}- {json.dumps(title, ensure_ascii=False)}: {page}")
    mkdocs.write_bytes(nl.join(lines).encode("utf-8"))
    return True


def build_html(repo_path: str) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _require_installed(repo)
    rc, out = _run([bash_exe(), (doc / "update.sh").as_posix(), "--html-only"], cwd=repo, timeout=900)
    problems = [l.strip() for l in out.splitlines() if re.search(r"\b(WARNING|ERROR)\b|Aborted|could not be found", l)]
    return {
        "ok": rc == 0,
        "index": str(doc / "html" / "index.html"),
        "problems": problems[:40],
        "output_tail": _tail(out),
        "hint": None if rc == 0 else
        "The previous html/ was kept. Fix the cause (nav, links, snippet paths); never loosen mkdocs.yml to get green.",
    }


def mark_synced(repo_path: str, area: str) -> dict[str, Any]:
    repo = resolve_repo(repo_path)
    doc = _require_installed(repo)
    _area_path(doc, area)
    rc, out = _git(repo, "rev-parse", "HEAD")
    if rc != 0 or not HASH_RE.match(out.strip()):
        raise SnapDoczillaError("The repo has no commits yet; commit something first.")
    (doc / f".last-sync-{area}").write_text(out.strip() + "\n", encoding="utf-8", newline="\n")
    return {"area": area, "last_sync": out.strip()}

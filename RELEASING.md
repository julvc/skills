# Releasing

Order matters: GitHub first, PyPI second, MCP registry last (the registry checks the PyPI package).
Needs: `git`, `python -m build`, `twine` (PyPI token), `mcp-publisher` (GitHub login).

1. **Push and merge.** One PR carries everything not yet in `main` (CMMI profile + user manual):
   ```bash
   git push -u origin feat/user-manual
   ```
   Open <https://github.com/julvc/skills/pull/new/feat/user-manual> (base `main`), wait for CI (`smoke`), merge.

2. **Tag.**
   ```bash
   git switch main && git pull
   git tag -a v1.2.0 -m "SnapDoczilla 1.2.0: user manual"
   git push origin v1.2.0
   ```

3. **GitHub release.** <https://github.com/julvc/skills/releases/new>, tag `v1.2.0`, paste the `## 1.2.0` section of
   `CHANGELOG.md` as notes. This is the notice existing users see.

4. **PyPI** (from `main`; builds fresh so old files are not re-uploaded):
   ```bash
   rm -rf dist && python -m build && python -m twine check dist/*
   python -m twine upload dist/*          # user: __token__, password: your PyPI token
   ```

5. **MCP registry** (needs 1.2.0 live on PyPI):
   ```bash
   mcp-publisher login github
   mcp-publisher publish
   ```

6. **Verify.**
   ```bash
   uvx snapdoczilla-mcp@1.2.0 --version      # 1.2.0
   ```
   Plugin users get the skill update from the new `main` (`.claude-plugin/plugin.json` is already `1.2.0`).

Version lives in four places that CI keeps equal: `src/snapdoczilla_mcp/__init__.py`, `server.json` (twice),
`.claude-plugin/plugin.json`.

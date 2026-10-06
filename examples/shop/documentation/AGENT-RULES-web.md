# Rules for the agent: UI component pages

Template for UI areas (Vue, React, Svelte, Angular, …). The skill copies it as `AGENT-RULES-<area>.md`
for each UI area. These rules apply on top of `AGENT-RULES.md` (including its language).

## Required structure of a component page

One page per component (`<area>/<name>.md`, added to `nav:`), with these sections in this order:

1. **What it is and what it's for** (2–4 lines a non-technical reader understands) + where it appears in the app.
2. **How it works** (Mermaid diagram or a short list; visible business rules).
3. **Component API**: tables of *Props*, *Events* and *Slots* (or the framework's equivalents): name, type, default, description. Taken from the code, never guessed.
4. **Usage example from this project** — required. REAL code from the repo.
5. **Source code** — required. REAL code from the repo.
6. **Things to know**: dependencies (hooks/composables, stores, constants, endpoints) and tech debt or non-obvious behavior.

## Embedding real code (never copy-paste)

`pymdownx.snippets` inserts the current file at build time, so the page never drifts.

````markdown
=== "Usage"

    ```tsx title="Screen.tsx"
    --8<-- "src/screens/Screen.tsx"
    ```

=== "Code"

    ```tsx title="Button.tsx"
    --8<-- "src/components/Button.tsx"
    ```
````

- Paths are relative to the repo root. Line range: `--8<-- "path:START:END"`.
- Prefer whole files. Use ranges only to pull one usage line out of a big file, and **re-check the range** whenever that file changes.
- Files over ~150 lines: wrap them in `??? note "Full source"` (content indented 4 spaces).
- Build fails with "snippet ... could not be found" → the file moved or was renamed: fix the path.
- An example that doesn't exist in the project must be labeled as illustrative.

## Maturity

If the component is incomplete (empty files, `console.log`, commented-out code), say so in a `!!! warning` block listing what's missing. Never document as working what doesn't work.

## No screenshots or live demos

They force running the app and go stale on their own.

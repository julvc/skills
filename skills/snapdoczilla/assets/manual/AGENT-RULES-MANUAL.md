# Rules for the agent: user manual

The user manual lives in `source/user-manual/` and is written for **end users**, not developers.
These rules apply on top of `AGENT-RULES.md` (including its language).

## Sources of truth

- **The UI code**: screens, menus, buttons, field labels, validations, confirmations and the messages the app shows
  (toasts, alerts, dialogs, error texts). Quote labels and messages **exactly** as the code renders them.
- README, release notes and existing docs (requirements, specs, CMMI artifacts) tell you *what* a function is for.
  Use them as reference, never as text to copy: they are written for developers or auditors.
- Anything you cannot verify in the code (a step that depends on external systems, a state no screen reaches)
  gets a `> ⚠️` "to be confirmed" note. Never describe a feature the code doesn't have.

## Pages

- `user-manual/index.md`: who the manual is for, requirements, how to get and open the app, first steps,
  a map of the screens (Mermaid), one line per function linking to its page, glossary, FAQ / troubleshooting,
  support contact (only if the code or README names one).
- One page per function or screen: `user-manual/<function>.md`, listed in `nav:` under the *User manual* section,
  right after `user-manual/index.md`. Sections in this order:
  1. **What it is for** (2–3 lines, business words).
  2. **Before you start** (data, files, permissions or settings it needs).
  3. **Step by step**: numbered steps in second person, one action per step, UI labels in **bold**.
  4. **Expected result** (what the user sees, files produced and where they are saved).
  5. **Messages and common problems**: table *Message → Cause → What to do*, taken from the real messages in the code.

## Style

- Second person, short sentences, the user's vocabulary. No source file names, function names, IPC, SQL or stack talk.
- Don't embed source code (`--8<--` is for technical pages). Formulas only when the user needs them to read a result
  (e.g. how a total is calculated), in plain words.
- Never copy real customer data, emails, tokens or keys shown in defaults or fixtures: use `{PLACEHOLDER}`.

## Screenshots

A human captures them (the agent doesn't run the app). Save them in `source/user-manual/img/` as `<function>-NN.png`.
A link to an image that doesn't exist fails the strict build, so:

- Image exists → `![Short description](img/<function>-NN.png)`.
- Image missing → leave a placeholder the human can act on, and keep going:

  ```markdown
  !!! note "📷 Screenshot pending: img/<function>-NN.png"
      What to capture: <screen, state, data to show>.
  ```

On every pass, replace the placeholders whose image now exists.

## Incremental updates

When a diff changes what users see or do (labels, steps, new buttons, messages, defaults, new screens),
update the matching manual pages. Internal refactors with no visible change don't touch the manual.
Flag screenshots that probably no longer match the screen with a `> ⚠️` note.

## CMMI profile (only when `AGENT-RULES.md` has a *CMMI profile* section)

- In `process-evidence.md`, add the manual to the evidence of **OT** (Organizational Training: end-user onboarding)
  and **VV** (the *Step by step* sections double as a validation walkthrough).
- In the traceability matrix, user-facing requirements may point their *Page* column to the manual page that covers them.
- The manual describes how the product is used. Never write that it was validated, tested with users or approved.

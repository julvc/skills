
## CMMI profile

This project uses SnapDoczilla's CMMI profile: the docs double as **objective evidence** for CMMI practice areas.
They support an appraisal; they never claim compliance or a maturity level by themselves.

- **`process-evidence.md`** (translate it to the documentation language on the first pass) maps each practice area
  to the page or repo artifact that shows it. Update a row only when its evidence changed; an area with no real
  evidence stays `⚠️ to be confirmed`, never filled with generic text.
- **ADRs follow Decision Analysis and Resolution (DAR):** `Status` (Proposed / Accepted / Superseded by NNNN),
  `Date`, `Deciders` (`{PLACEHOLDER}` if unknown), `Context`, `Decision criteria`, `Alternatives considered`
  (at least two, each evaluated against the criteria), `Decision`, `Consequences`. Alternatives you cannot find
  in the code, commits or existing docs get a `> ⚠️` note; never invent the rejected options.
- **Traceability (RDM / VV):** keep the matrix in `process-evidence.md` as *Requirement → Code → Tests → Page*.
  Requirement IDs come only from real sources (commit messages, branch names, issue links, existing specs,
  e.g. `PROJ-123`). No IDs in the repo → leave the matrix empty with a `> ⚠️` note; never make IDs up.
- **Configuration management (CM):** on each release tag, add a row to *Baselines* (tag, date, commit, docs sync).
  Find tags with `git tag --sort=-creatordate`.
- **Peer reviews (PR):** docs changes reach the main branch through a reviewed pull request. Never write that
  something was reviewed or approved; reviewers are recorded by the git host, not by you.

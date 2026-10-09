# Process evidence (CMMI)

> This page maps CMMI practice areas to the evidence that lives in this repository.
> It supports an appraisal; it is not a statement of compliance or maturity level.
> File names in `code` become links once that page exists (a link to a missing page fails the build).

## Evidence map

| Practice area | Evidence in this repo | Status |
|---|---|---|
| TS - Technical Solution | `architecture.md`, ADRs in `adr/` | ⚠️ to be confirmed |
| DAR - Decision Analysis and Resolution | ADRs with criteria and alternatives (`adr/`) | ⚠️ to be confirmed |
| PI - Product Integration | Integrations in `architecture.md`, build steps in `getting-started.md` | ⚠️ to be confirmed |
| RDM - Requirements Development and Management | [Traceability](#traceability) | ⚠️ to be confirmed |
| VV - Verification and Validation | Test commands in `getting-started.md`, *Tests* column in [Traceability](#traceability) | ⚠️ to be confirmed |
| PR - Peer Reviews | Pull requests that change `documentation/` (git host history) | ⚠️ to be confirmed |
| CM - Configuration Management | Git history, `.last-sync-*` markers, [Baselines](#baselines) | ⚠️ to be confirmed |
| PQA - Process Quality Assurance | `--strict` docs build, `.githooks/pre-push` reminder | ⚠️ to be confirmed |
| OT - Organizational Training | [Home](index.md) and `getting-started.md` as onboarding | ⚠️ to be confirmed |
| PAD - Process Asset Development | `documentation/AGENT-RULES*.md` (standard docs process) | ⚠️ to be confirmed |

Not covered here (they live in project-management tools; link them if the team wants): planning, estimating,
monitoring and control, risk and opportunity management, supplier management, governance.

## Traceability

| Requirement | Code | Tests | Page |
|---|---|---|---|

> ⚠️ To be filled from real requirement IDs (commits, branches, issues).

## Baselines

| Tag | Date | Commit | Docs sync |
|---|---|---|---|

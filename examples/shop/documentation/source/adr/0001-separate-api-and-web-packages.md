# ADR 0001: Separate API and web packages

**Status:** Accepted (reconstructed from the code)

## Context

The shop needs a product backend and a browser UI.

> ⚠️ To be confirmed: the original reasons were not recorded; this ADR documents what the code shows.

## Decision

- Two independent npm packages in one repo: `api/` (Express 4) and `web/` (React 18 + Vite 5).
- They share no code; they communicate only over HTTP (`/api/productos`).
- Products are kept in an in-memory array for now.

## Consequences

- Each part installs and runs on its own.
- Data does not survive an API restart until a real database is added (that would deserve its own ADR).
- The web dev server needs a proxy or CORS to reach the API on port 3000; neither is configured yet.

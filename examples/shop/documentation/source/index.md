# Shop

Small product catalog: a REST API that stores products and a web page that lists them as cards with an "add" button.

Code identifiers are in Spanish (`productos` = products, `nombre` = name, `precio` = price, `Agregar` = Add, `Catalogo` = Catalog). This documentation keeps them verbatim.

## Repository layout

| Folder | Package | What it is |
|---|---|---|
| `api/` | `tienda-api` | Node.js + Express REST API |
| `web/` | `tienda-web` | React single-page frontend built with Vite |

## Stack and versions

Versions are the ranges declared in each `package.json` (no lockfile is committed).

| Area | Technology | Version |
|---|---|---|
| api | Express | `^4.19.0` |
| web | React / React DOM | `^18.3.0` |
| web | Vite (dev) | `^5.0.0` |

> ⚠️ To be confirmed: required Node.js version (no `engines` field, no `.nvmrc`).

## Where to go next

- [Getting started](getting-started.md): run both parts locally.
- [Architecture](architecture.md): how the pieces talk to each other.
- [API](api.md): endpoints.
- [ProductCard](web/ProductCard.md): the product card component.

---
Last sync: f36fa42 (2026-10-06)

# Architecture

Two independent packages with no shared code: a browser app and a REST API.

```mermaid
flowchart LR
    subgraph web["web/ (React + Vite)"]
        C[Catalogo page] --> PC[ProductCard x N]
    end
    subgraph api["api/ (Express, port 3000)"]
        R["/api/productos router"] --> DB[("in-memory array")]
    end
    C -- "GET /api/productos" --> R
```

## API layers

| Layer | File | Responsibility |
|---|---|---|
| App | `api/src/index.js` | Creates the Express app, enables JSON bodies, mounts the router, listens on 3000 |
| Routes | `api/src/routes/productos.js` | Product endpoints and the data store |
| Storage | `const db = []` in the router | In-memory array; **data is lost on every restart** |

There is no service layer, database, validation, authentication or external integration.

## Web structure

| Path | Role |
|---|---|
| `web/src/pages/Catalogo.jsx` | Page: loads products once and renders one card each |
| `web/src/components/ProductCard.jsx` | Presentational card: [ProductCard](web/ProductCard.md) |

State is local component state (`useState`); there is no global store or router.

## Main flow: show the catalog

```mermaid
sequenceDiagram
    participant U as Browser
    participant C as Catalogo
    participant A as API
    C->>A: GET /api/productos (on mount)
    A-->>C: 200 [ {nombre, precio, ...} ]
    C->>U: one ProductCard per product
    U->>C: click "Agregar"
    C->>C: console.log(nombre)
```

> ⚠️ "Agregar" (add) only logs the product name. No cart exists yet.

# API

Base URL: `http://localhost:3000`. JSON in and out. No authentication.

## Products — `/api/productos`

| Method | Path | Body | Response | Notes |
|---|---|---|---|---|
| `GET` | `/api/productos` | — | `200` array of products | Returns everything stored since the last restart |
| `POST` | `/api/productos` | product JSON | `201` the same body | Stored as received, **no validation** |
| `DELETE` | `/api/productos/:id` | — | `204` | **Does nothing**: always returns 204, deletes no data |

### Product shape

There is no schema. The only fields the frontend reads are:

| Field | Type | Used by |
|---|---|---|
| `nombre` | string | card title, React `key`, value passed to `onAgregar` |
| `precio` | number or string | card price |

> ⚠️ To be confirmed: products have no `id`, so it is unclear what `:id` in `DELETE` should refer to.

### Example

```bash
curl -X POST http://localhost:3000/api/productos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Coffee","precio":4500}'
```

## Source

```js title="api/src/routes/productos.js"
--8<-- "api/src/routes/productos.js"
```

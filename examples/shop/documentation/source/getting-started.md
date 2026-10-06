# Getting started

There is no README in the repo; everything below comes from the `package.json` files.

## Requirements

- Node.js and npm.

> ⚠️ To be confirmed: minimum Node.js version.

## API

```bash
cd api
npm install
npm start          # node src/index.js -> http://localhost:3000
```

The port is hard-coded to `3000` in `api/src/index.js`; there are no environment variables or config files.

## Web

```bash
cd web
npm install
npm run dev        # vite dev server
```

!!! warning "The web app is not runnable yet"
    - `web/` has no `index.html` and no entry file that mounts React (e.g. `main.jsx`), so Vite has nothing to serve.
    - Nothing renders the `Catalogo` page; there is no router.
    - `Catalogo` calls `fetch("/api/productos")` with a relative URL, but there is no `vite.config.*` proxy to the API on port 3000.

## Tests

No test scripts or test files exist in either package.

## Build

Only the `dev` script exists in `web/`; there is no `build` script. The API has no build step.

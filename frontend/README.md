# OmniKPI frontend

React/Vite SPA for divisional performance reporting: review report mappings, compare KPI readings, trace their source and review evidence-linked explanations. The approved navy/blue UI supports light/dark themes, keyboard access and reduced motion.

## Install and run

Use Node 24 (validated with 24.13.0) and npm. The toolchain requires Node `^20.19.0 || >=22.12.0`. From this directory:

```powershell
npm.cmd ci
npm.cmd run dev:audit
```

The safe UI-only server runs at `http://127.0.0.1:5173`, disables environment-file loading and has no API proxy. Use the synthetic Playwright fixtures for populated states; a live backend is not needed for frontend validation. No environment file is required for these checks.

`npm.cmd run dev` retains the existing `/api` proxy to `http://127.0.0.1:8000`. Use it only with a separately authorized backend; a localhost address alone does not establish authorization or data isolation. Never use production records for UI testing.

## Commands

| Command | Purpose |
| --- | --- |
| `npm.cmd run typecheck` | Check TSX and shared types; existing JS remains supported |
| `npm.cmd run lint` | Lint maintained source and scripts |
| `npm.cmd test` | Six mocked frontend API-contract tests |
| `npm.cmd run build:ui` | Production build with environment-file loading disabled |
| `npm.cmd run preview:audit` | Static UI-only preview at `127.0.0.1:5176`, no proxy |
| `npm.cmd run build` / `preview` | Existing standard Vite commands; normal config/env behavior |
| `npm.cmd audit` / `npm.cmd audit --omit=dev` | Full / runtime dependency advisory checks |

On shells without the PowerShell execution-policy issue, `npm` also works. Do not change system execution policy to run npm scripts.

## Project notes

- Routes: `/` landing, `/app` workspace; `?demo=1` selects the existing demo API namespace. “Try demo” makes the existing seed POST; safe browser tests intercept it.
- Stack: React 19, Vite 8, Tailwind 4, Motion, Recharts, Three.js and source-integrated React Bits. Shared TSX primitives use `src/components/ui`; `@/` maps to `src` through Vite and TypeScript. `components.json` preserves shadcn-compatible paths.
- [Development and browser testing](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md), [isolated integration plan](docs/INTEGRATION.md), [approved design](DESIGN.md).
- Synthetic downloadable reports and their validation instructions remain under `public/demo/`. Preserve their values and checksums.
- Preserve [React Bits license terms](REACT_BITS_LICENSE.md), `public/react-bits-license.txt` and `public/licenses/` when distributing the frontend. These components are not a separately redistributable component library.

Visual approval and passing frontend tests do **not** establish overall production readiness. An authorized isolated-backend integration run, agreed timeout/error contracts and failed lazy-chunk recovery remain release conditions; see the integration plan. No merge or deployment is authorized by local cleanup.

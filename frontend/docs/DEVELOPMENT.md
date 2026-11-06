# Local development and validation

Use `npm.cmd ci` from the frontend root. Commit package/lock changes together only after separate Git authorization; do not upgrade versions during cleanup. `npm.cmd run dev:audit` serves the UI at loopback 5173 without environment files or an API proxy. `npm.cmd run build:ui` uses the real build config with environment loading disabled. `npm.cmd run preview:audit` serves `dist` at loopback 5176 with no proxy. Ordinary `dev`/`build`/`preview` retain their original behavior.

Never inspect `.env`/credentials, real records or backend/database files for UI testing. Do not run migrations, production pages or sensitive services. Use local synthetic browser fixtures. The safe servers do not seed a backend: their Try demo action needs a Playwright intercept or a separately authorized environment. See [INTEGRATION.md](INTEGRATION.md).

## Checks

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd test
npm.cmd run build:ui
npm.cmd audit
npm.cmd audit --omit=dev
npm.cmd ls --all
```

The API tests use Node's test runner and mocked fetch, not real HTTP. Lint excludes installed agent packages, generated outputs and local maintenance helpers, not application source or maintained tests.

## Playwright

Existing scripts reuse an installed Playwright runtime (including the Playwright MCP installation), avoiding an application runtime dependency. The runtime and browser binaries must already be available; `npm ci` installs frontend packages, not external browser binaries. Supply the installed runtime's absolute `index.mjs` path and a cached Chromium executable where required. Never hardcode a developer-specific cache path in shared source. Record the actual runtime/browser versions with release evidence.

With `preview:audit` running, the canonical synthetic full-application regression covers desktop/tablet/mobile, light/dark, keyboard/dialog behavior, forms, error/loading/empty states and reduced motion:

```powershell
node scripts/ui-cross-browser.mjs <playwright-index.mjs> chromium firefox webkit --chromium-executable=<chrome.exe>
```

With `dev:audit` running, run focused current landing checks:

```powershell
node scripts/problem-panels-check.mjs <playwright-index.mjs> <chrome.exe> after
node scripts/workflow-timeline-check.mjs <playwright-index.mjs> <chrome.exe> after
node scripts/traceability-check.mjs <playwright-index.mjs> <chrome.exe> after
node scripts/landing-minimal-polish-check.mjs <playwright-index.mjs> <chrome.exe> after
node scripts/landing-buttons-motion-check.mjs <playwright-index.mjs> <chrome.exe>
node scripts/landing-buttons-touch-check.mjs <playwright-index.mjs> <chrome.exe>
node scripts/landing-polish-check.mjs <playwright-index.mjs> <chrome.exe>
node scripts/requested-ui-fixes-check.mjs <playwright-index.mjs> <chrome.exe>
node scripts/landing-react-bits-check.mjs <playwright-index.mjs> <chrome.exe>
```

`color-bends-check.mjs` targets preview 5176 and tests WebGL/fallback/chunk behavior. `ui-stress.mjs` and `ui-touch-gestures.mjs` export Page-based synthetic validators for long-content/text-enlargement and touch interactions. Retain them; viewport-only checks do not replace these scenarios. All current test fixtures remain embedded in maintained scripts or public synthetic examples. A selector-only test repair must preserve its behavioral assertion.

Review actual screenshots as well as assertions. New outputs go to ignored `artifacts/`, `test-results/` or `playwright-report/`. Historical outputs and packaging/audit scripts were moved to a verified external archive, not discarded; they are not needed to build or run current regressions. Keep unique approved evidence before replacing an output directory. Historical gallery/ZIP regeneration requires restoring its original inputs from that archive.

## Maintenance boundaries

- Keep `README.md`, root `DESIGN.md`, legal notices, and these operational docs; put future implementation history in local review evidence rather than accumulating root Markdown reports.
- Agent instructions/configuration remain on disk but ignored (`AGENTS.md`, `.agents`, `.codex`, `.claude`, `.impeccable`, skills lock). Do not remove trusted tools or repair their internals as incidental cleanup.
- Keep `node_modules`, build outputs, coverage, logs, caches, environment files and credentials out of Git. Example environment files may be versioned only after content review. Ignore rules do not untrack already tracked files; index changes require separate authorization.
- Preserve public licenses and synthetic validation data. Unused exported button variants remain part of the supplied shared API; static non-use alone is not permission to remove them. Legacy style compatibility remains until computed-style equivalence can be proven.
- Cleanup never authorizes Git staging, branches, commits, pushes, merges or deployment. Overall release assessment remains subject to the integration and recovery conditions in [ARCHITECTURE.md](ARCHITECTURE.md).

# Frontend architecture

`main.jsx` initializes the saved `omnikpi-theme`, wraps the SPA in MotionConfig/BrowserRouter, and mounts `AppRoutes`. The landing route is eager; the workspace is lazy behind a visible Suspense status. History/Recharts and the hero's Three.js effect load in separate chunks. This separation is intentional; do not pull charts or Three.js into the initial entry for cleanup.

`Landing.jsx` composes existing marketing components and the unchanged demo seed handler. `ProblemSection`, `WorkflowSteps` and `TraceabilitySection` own narrowly scoped presentation. Source-integrated React Bits: ColorBends, BorderGlow and CardNav. CinematicText replaced the earlier unused BlurText. Arc's theme switch and the shared button primitives retain their source notices and interaction semantics.

`App.jsx` coordinates workspace filters, selections and dialogs. `HeatmapMatrix`, `KPIDetailModal`, `HarvesterModal`, `RCAPanel` and the shared `Dialog` retain the approved table, chart, upload, mapping and investigation flows. `src/api/client.js` owns query encoding and fetch requests; its base switches from `/api/v1` to `/api/demo/workspace/api/v1` for `demo=1`. Authentication requirements belong to the backend contract and are not assumed absent.

Tailwind 4 is configured in `src/index.css` and the Vite plugin, not a Tailwind 3 configuration file. Semantic tokens and compatibility utilities coexist intentionally. Component-specific styles are scoped. Some legacy overrides remain: do not delete a class merely because static search misses dynamically composed utility names.

All application runtime packages remain used: React/DOM/Router, Motion, Recharts, Three.js, Lucide, Hugeicons, Radix Slot, CVA, clsx and tailwind-merge. Vite/plugins, Tailwind, TypeScript/types and oxlint are development tooling. Explicit Windows native optional bindings are retained for the validated toolchain. No dependency upgrade/removal was needed during repository cleanup.

## Known release conditions

- **High assurance gap:** no authorized isolated-backend integration run. Ownership/auth/CSRF, parser/import persistence, conflict prevention and AI-provider behavior remain unverified.
- **Medium:** workspace fetches lack an agreed timeout/cancellation policy; error details are not fully normalized; successful API responses expect JSON, including a contract question for 204. Do not add automatic mutation retries. The separate landing seed action already has a 30-second frontend timeout/recovery path.
- **Medium:** failed lazy chunks lack a dedicated error boundary/reload path. Keep existing loading states and validate recovery against an agreed release requirement.
- **Medium validation limits:** simulated Chromium/Firefox/WebKit do not certify physical devices, native Safari hardware, screen-reader behavior or hosting/security configuration.
- **Low:** the existing optional ColorBends chunk exceeds the default 500kB warning threshold. It remains lazy, reduced-motion-aware and separate from the entry.

Zero advisory findings and approved visuals are not complete application security or production certification. Backend execution stays blocked until the environment and permissions in [INTEGRATION.md](INTEGRATION.md) are supplied. No backend change is part of frontend maintenance.

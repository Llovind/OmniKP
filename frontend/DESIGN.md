# Approved OmniKPI design

Preserve the current UI: navy/blue identity, Segoe UI/system typography, quiet surfaces, readable data density, light/dark themes and restrained motion. The user approved the V2 baseline and subsequent scoped landing refinements. Maintenance is not authorization for another redesign.

## Foundation

Semantic CSS tokens in `src/index.css` are authoritative: `--page`, `--surface`, `--subtle`, `--ink`, `--muted`, `--line`, `--control-line`, `--accent`, `--on-accent`, `--red`, `--green`, `--amber`. Light foundation: page `#f3f6fb`, ink `#102c4d`, accent `#0864c9`; dark: page `#0c1727`, ink `#e5eefb`, accent `#77b5ff`. Borders distinguish separators from interactive boundaries. Do not replace theme-aware chart/status colors with fixed low-contrast colors.

Use the existing 4/8/12/16/24/32/48px spacing rhythm, tabular numeric readings, visible focus rings and practical 44px interaction targets. Dense data remains readable at 14px primary / 12px context. New styles should be scoped and reuse semantic tokens. Native semantic controls and shared `Dialog` own interaction behavior.

## Accepted composition

- Centered fixed CardNav; cinematic hero with liquid-glass actions and lazy blue ColorBends, with a safe static fallback.
- Three soft problem panels with exact supplied copy; connected numbered workflow, horizontal at desktop/tablet and vertical on mobile.
- Two BorderGlow AI capability cards; native provenance ZIP download and a structured 97.8% synthetic provenance card. Keep the distinction between AI assistance and deterministic validation.
- Human review statement and closing blue demo action; approved text, KPI values, source data and section order remain intact.
- Workspace filters, contained heatmap/ledger scrolling, opaque sticky heatmap headers, readable history charts and accessible upload/mapping/history dialogs. Preserve focus management, reduced motion and API contracts.

## Motion

Use the installed Motion package and existing CSS feedback; add no new animation library. Buttons/hover feedback typically 120–220ms, overlays 180–320ms, route/section settling about 200–350ms, travel generally 4–8px. Existing workflow connectors draw once over 500ms. Cap entrance staggers; do not replay on scroll-back, bounce, animate numeric readings or animate dense data rows.

Reduced motion must preserve information with static alternatives, including live preference changes where implemented. Pause decorative WebGL work offscreen/hidden and fall back when unavailable. Existing hero/BorderGlow effects are specifically approved; do not expand them into other sections. No additional gradients, glows, glass, particles or parallax without specific review feedback.

## Deferred, non-blocking backlog

These Low-priority items require specific future authorization: mobile mapping-table scroll discoverability; clearer compact KPI abbreviation affordances; a more focused, legible mobile landing preview. Do not implement them automatically.

Historical approval ZIPs, screenshot galleries and detailed reports are preserved in a local external archive recorded by the ignored `CLEANUP_REPORT.md`. They are historical evidence, not build inputs. Current test fixtures and scripts remain in the project; use fresh captures to verify maintenance.

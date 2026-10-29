# OmniKPI frontend

React/Vite SPA for divisional report consolidation and performance review.
Run npm install and npm run dev; Vite forwards /api to http://127.0.0.1:8000.

The main screen defaults to confirmed division submissions. Use the upload dialog
to review mappings, validate every reading, and confirm import. Downloadable
synthetic examples cover row and wide location layouts. Colors represent target
attainment, while Z-scores are supplementary history context.

Select a reading to inspect its source, history and division feedback. RCA drafts
cite submitted feedback; missing feedback returns an insufficient-evidence result.

Use npm run lint and npm run build for frontend checks. Production hosting needs
its own /api reverse proxy. See the root README for the demo walkthrough and limits.

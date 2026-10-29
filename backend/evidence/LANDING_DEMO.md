# Landing and demo delivery

Start FastAPI from backend with `python -m uvicorn main:app --reload --port 8000`.
Start Vite from frontend with `npm.cmd run dev`. Visit http://localhost:5173/.

Routes: `/` product landing; `/app` existing workspace; `/app?demo=1` isolated synthetic workspace after POST `/api/demo/seed`. Reset uses POST `/api/demo/seed?reset=true`.

Demo storage: backend/omnikpi-demo.db, completely separate from the normal database. Reuses existing stage, validation, confirmation, feedback and reporting services. The seven pre-reviewed fixture files are imported locally without model calls. Existing synthetic feedback is imported with its source rows. Reset clears only this demo database. The demo is shared by visitors to the same server; one visitor's reset resets that shared synthetic workspace. Production hosting should keep this route demo-only.

Assumption: footer competition is ITASE 7.0. The user's specified visual patterns and copy override AntiSlop defaults regarding pill navigation, the eyebrow, and the requested three problem blocks. Font, logo and theme variables are reused. Landing styles are scoped; no workspace redesign was performed.

Checks: eleven backend integration tests, lint and build. Chrome browser check covers Try demo, 180 visible readings, reset, landing screenshots at 390/768/1440 and horizontal overflow. Real screenshot saved to frontend/public/landing/workspace.png. Lighthouse accessibility score: 100 in the local light-theme run, recorded in landing-lighthouse.json. No production-host or multi-user load validation was performed.

Hosting must serve index.html for frontend routes such as /app and proxy /api to FastAPI. The existing Vite dev proxy already handles API routes. No deployment or commit was made.

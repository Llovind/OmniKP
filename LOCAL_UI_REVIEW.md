# Local UI branch review

Source: origin/style/ui-refinement-v2, commit 527447b.
Local branch: review/ui-refinement-v2.
Worktree: C:\KPI_Dashboard_UI_Review.

Local recovery changes, currently uncommitted:

- Added frontend/src/lib/utils.ts for the cn imports required by the UI buttons.
- Added a root ignore exception for frontend/src/lib, so the new utility can be committed.
- Removed the frontend scripts/ ignore rule so actual source scripts can be tracked later.
- Removed package commands pointing to missing scripts. Those tests and audit helpers were not restored or executed; the branch author should supply their actual files before restoring the commands.
- Synchronized package-lock.json after clean installation reported missing @emnapi entries.

Validated with Node 24.22.1: production build, oxlint, TypeScript, and npm ci dry-run passed. Build reports a non-fatal chunk-size warning for the deferred Three.js visual.

Backend runs from this worktree on 127.0.0.1:8000. Frontend runs on 127.0.0.1:5174, using the existing API proxy. The worktree has its own local SQLite files. The user's existing AI router key, base URL and model were subsequently copied into ignored backend/.env. No database configuration was copied and credentials are not exposed in the status endpoint or reports.

AI workflow recovery: explicit AI mapping bypasses saved mapping memory and permits a preview of already imported synthetic inputs. The normal validation and confirmation gates still reject duplicate readings. The workspace now offers an AI mapping entry point and an ED feedback RCA shortcut; both outputs distinguish model generation from local fallback. Synthetic sample selection enables the visible AI checkbox; ordinary uploads retain opt-in behavior.

Live provider checks succeeded with gemini-flash-lite-latest: ED produced seven LLM column suggestions; confirmation was blocked for the already imported readings. The ED RCA returned ai_draft with feedback citation F1. These calls used only synthetic fixture content. Twelve existing backend tests passed after the intake change.

GET health and POST demo seed through the frontend proxy succeeded. The seeded heatmap contains two locations with 90 readings each: 121 meeting target and 59 missing target in total. These are API smoke checks, not browser interaction or visual QA.

Open http://127.0.0.1:5174/ or http://127.0.0.1:5174/app?demo=1 while the local servers are running.

For subsequent starts, use Node 24 or a supported Node version (^20.19 or >=22.12), then npm run dev -- --host 127.0.0.1 --port 5174 --strictPort in frontend, and python -m uvicorn main:app --host 127.0.0.1 --port 8000 in backend.

The workstation's default Node 22.6.0 is too old for this branch. Current processes use the bundled Node 24.22.1 explicitly. The branch's older frontend docs reference absent audit scripts and should not be treated as runnable commands until their sources are supplied.

No merge, commit, push, or deployment has been performed.
# Integration status

The reviewed UI and mandatory live AI workflow are now integrated in
`C:\KPI_Dashboard` with remote main through `43af967`. The original UI checkpoint
is `dc73f39`. The notes below describe the earlier isolated review and may refer
to its previous branch state. Current behavior is described in `AI_WORKFLOW.md`.


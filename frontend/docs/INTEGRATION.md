# Isolated backend integration plan

Status: frontend-only contracts inspected and synthetic tests executed. **Real backend integration is blocked.** No approved isolated backend URL, synthetic account/authorization procedure, API specification or disposable dataset lifecycle has been supplied. A localhost proxy target is not evidence of isolation or authorization. No backend files, secrets, records or databases were inspected.

## Required environment

Provide an explicitly authorized loopback/staging API origin, confirmation that it cannot reach production records, synthetic-only identities with two different division roles, a backend-owner-managed fixture/reset process, documented authentication/CSRF and response schemas, and allowed mutation scope. Share test identities through an approved secret mechanism, not frontend source or reports. The backend owner provisions/resets the dataset; this plan does not authorize migrations or direct database access. Agree timeout and retry budgets for parser/AI operations before changing frontend request behavior.

## Frontend contract inventory

API base: /api/v1, or /api/demo/workspace/api/v1 when demo=1. Domain is currently fixed to 1. Fetch defaults to same-origin credentials; there is no frontend bearer-token injection or explicit CSRF header. Authentication/authorization requirements are **unknown**, not proven absent. Same-origin proxy/hosting and backend policy must be verified. React text rendering is used for displayed messages; no raw response HTML rendering was found in the inspected layer.

| Method/path relative to base | Request | Fields required by UI / expected contract |
| --- | --- | --- |
| GET /domains | None | Wrapper exists; not used by current representative routes; schema requires backend spec |
| GET /domains/:id/kpis, /locations, /anomalies | Optional anomalies query | Wrappers exist; active route usage not observed; schemas not assumed |
| GET /domains/:id/heatmap | dataset, division, date query; blank values omitted | date, locations[] containing location_id/name/type, summary total/red/yellow/green, kpis[] with IDs, values, unit, direction, status, z_score, provenance/division |
| GET /domains/:id/periods | dataset, division query | Date-string array |
| GET /domains/:id/submissions | None | Array of submission_id, division, filename, report_date, readings |
| GET /domains/:id/kpis/:kpiId/history | location_id, as_of | history[] date/actual_value/target_value/status/z_score; optional target_threshold/higher_is_better |
| POST /domains/:id/rca | JSON kpi_id, location_id, fact_id | evidence_status, root_cause, prescriptive_action, evidence[] (feedback_id/division/explanation/corrective_action), llm_model |
| POST /domains/:id/submissions/preview | FormData file, division, report_date, sheet_name, header_row, header_depth, use_ai | submission_id, division, filename, rows_parsed, sheet_name, header_row, columns[], column_mapping targets/methods, raw_preview[], message |
| POST /domains/:id/submissions/:submissionId/review | JSON mapping, default_direction | can_confirm, valid_readings, invalid_readings, conflict_count, issues[], conflicts[], preview[] |
| POST /domains/:id/submissions/:submissionId/confirm | Same reviewed JSON mapping/direction | dates[], readings_imported, division |
| POST /domains/:id/feedback | JSON fact_id, explanation, corrective_action | JSON success body currently required; feedback then RCA/heatmap refresh |
| POST /api/demo/seed and ?reset=true | No body, outside base | Landing/Header check HTTP success and navigate; write/reset must be authorized even in a demo |

Static catalogue/download requests: /demo/divisions/manifest.json and files named by it. They are frontend assets, not proof of authorized backend fixtures. Do not use existing workbook contents in isolated tests; generate new synthetic CSVs.

## Current behavior and gaps

Workspace fetches heatmap/periods/submissions in parallel. Loading status, empty state and error/Retry exist; one failed parallel request fails the group. No explicit client timeout or cancellation signal; stalled reads and writes can leave loading/busy states indefinitely. Intake close is disabled while busy. Mutations are not automatically retried (verified), which avoids accidental duplicate import on uncertain outcomes.

Non-2xx JSON detail is surfaced; non-JSON failure falls back to statusText/HTTP code. Structured detail arrays/objects are not normalized; success bodies are always parsed as JSON (including possible 204). No successful-empty-body or unknown-schema compatibility is claimed. Schema validation is not performed at runtime. UI state cancellation guards suppress some obsolete updates, but do not abort requests. Filters are component state, not fully deep-linked. These are frontend integration risks to test, not confirmed backend incidents.

## Execution matrix for the authorized environment

| Test | Synthetic setup/action | Required evidence |
| --- | --- | --- |
| Authentication and ownership | Anonymous, expired session, division A/B accounts | Expected 401/403; A cannot read/write B's data; CSRF and logout policy confirmed by backend owner |
| Read/empty/filter/history | Two divisions, two dates, mixed RED/YELLOW/GREEN, missing target/baseline | Actual schemas accepted; totals and ledger match filters; history respects location/as_of; empty and loading states work |
| Preview and review | New CSV with known unit/direction/actual/target; malformed headers and missing values | No imported reading before explicit confirmation; mapping correction and actionable row errors |
| Confirm/replay/concurrency | Validated mapping; change mapping after review; duplicate concurrent requests | Revalidation required; backend rejects invalid/conflicting inputs; duplicate prevention verified through API, never direct DB queries |
| Feedback/RCA | Evidence absent, then synthetic attributable feedback; unavailable AI | Insufficient-evidence response, owned attribution, model/fallback policy; provider calls only if separately authorized |
| Failure handling | Controlled 400/401/403/409/422/429/500/503, offline, non-JSON gateway, 204, slow/hung requests | Clear errors, retained inputs, known outcome before retrying mutations; agreed timeout behavior |
| Navigation/network | Fresh landing → workspace → history, back/refresh, unavailable lazy chunk | Visible loading; recovery path; confirm missing chunk boundary before release |

Completed without backend: six Node API contract tests (query encoding, history parameters, separate review/confirm, FormData boundary, JSON/non-JSON failures, offline/no mutation retry); Playwright synthetic UI flow at three widths including confirmation gate invalidation, feedback, 503/Retry, accessibility and reduced motion. **None of these are real backend integration results.**

Release evidence must record backend build/version, fixture IDs, test timestamp, response status/schema assertions and anonymized failures. Do not store cookies, tokens, uploaded real files or response personal data. Stop only backend execution until the required isolated environment is provided; frontend testing can continue.

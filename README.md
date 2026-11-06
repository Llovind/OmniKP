# OmniKPI — Telco KPI Consolidation & Performance Review

OmniKPI is a competition prototype inspired by Performance & Support teams that
collect Excel reports from multiple telco divisions, combine them manually, check
targets and prepare RCA with feedback from the responsible division.

The implemented workflow is **upload → review mappings → validate → confirm →
central dashboard → division feedback → evidence-linked RCA draft**.

## What works now

- **Division intake:** .xlsx and UTF-8 .csv, one worksheet per upload. Supports
  rows per reading and wide location columns, with one to three header levels.
- **Schema interpretation:** local header aliases and fuzzy matching; opt-in
  pretrained AI uses headers plus up to three bounded sample values per column.
  Review and correct every proposed meaning before confirmation.
- **Auditable AI suggestions:** each proposal carries a short reason, and every
  response includes the trace actually used — mode (`live`, `recorded`, `skipped`),
  model, column and sample scope, batches and latency. With no provider key, the
  seven demo layouts replay recorded suggestions that are labelled
  “AI suggestion · recorded”; recorded output is never presented as a live call.
- **Mapping evaluation:** `/evaluation` and `GET /api/v1/ai/evaluation` publish the
  synthetic five-layout comparison of local rules versus the configured provider.
  `GET /api/v1/ai/status` reports what the running build will actually do.
- **Mapping memory:** confirmed column mappings are reused for the same division
  and exact ordered header signature. Changed layouts receive new suggestions.
- **Validation:** missing/non-finite values, incompatible units/directions,
  invalid dates, duplicate readings and conflicts block the entire import.
  Nothing is written to fact_kpi until confirmation succeeds.
- **Central data:** new KPIs/locations can be registered during confirmation;
  every imported reading retains its division, filename and source row.
- **Dashboard:** union of all reported KPI sets, reporting-date and division
  filters, source attribution and a confirmed submission ledger. Missing data is
  not carried forward or shown as a healthy zero.
- **Target attainment:** red means target missed, green means target met, yellow
  means target unavailable. Higher/lower-is-better and per-reading targets apply.
- **Historical context:** imported series use prior readings within a 30-calendar-day
  window (minimum ten). Backfills recompute the affected series, including later
  readings. Constant/insufficient baselines have no Z-score. Statistical anomalies
  remain separate from target attainment.
- **RCA:** feedback belongs to an exact KPI/location/date reading. Without it the
  server returns “Bukti Tidak Cukup” without calling an LLM. With feedback, it can
  generate an advisory draft that cites feedback IDs. Invalid/missing citations or
  provider failure fall back to attributed feedback excerpts. No numerical
  confidence percentage is shown. Responses also state whether the model was
  invoked and how many claims lacked a feedback reference.

## Try the demo

### Workbook-based division demo

Download the **validation pack** from the landing page or upload dialog. It includes
the seven synthetic inputs, an independently calculated expected consolidated
workbook, per-reading JSON reference, checksums, and three separate failure exercises.
The reference totals are 180 readings: 121 meeting target and 59 missing target.
See `frontend/public/demo/divisions/VALIDATE.md` for the step-by-step comparison.

For frontend handoff: use Node 22.12+ (or Node 20.19+), run `npm ci` in frontend,
and keep FastAPI on port 8000. `/app` uses the normal database; `/app?demo=1`
uses the isolated seeded database. The private source workbooks are not required
to run the application or tests. Preserve API request/response contracts when
changing the interface. `DESIGN.md` records the agreed visual direction.

Use **Upload report → Division demo workbooks**. Seven downloadable Excel reports
follow the June WISA workbook's `SUB-UNIT REG BARU` grouping: BGES & OLO (41 KPIs),
MBB (17), ED (13), NETOP OSP (8), FBB (8), AIM (2), and DEFA (1).
Each **Load** button selects the file and fills its unit, sheet, header row and
reporting date. Interpret, validate and confirm each report. All seven together
produce 180 readings for 90 KPIs at two synthetic locations on 2026-06-30.
Definitions and ownership follow the source; readings, targets and feedback are
synthetic. These are reconstructed demo inputs, not original divisional files.
See `backend/evidence/division-demo/README.md` for provenance and reconciliation.

Wide AI mappings now use batches of 60 columns rather than rejecting files over
80 columns. The existing 300-column parser limit remains. Consolidated WISA outputs
are identified separately because they cannot safely be attributed to one unit.
The older CSV examples below remain available as minimal technical samples.

Start the backend:

~~~powershell
cd backend
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn main:app --reload --port 8000
~~~

Start the frontend in another terminal:

~~~powershell
cd frontend
npm install
npm run dev
~~~

Open http://localhost:5173. An existing local database is preserved; startup only
creates missing tables and the telco domain. AI provider/model settings come from
backend/.env. Manual mapping and evidence summaries work without an API key.

1. Download the synthetic **rows per reading** sample from the empty dashboard or
   upload dialog. Submit it as **Mobile Broadband**.
2. Review the mappings and original values; validate, then confirm six readings.
3. Download the **location columns** sample and submit it as **Fiber Connectivity**.
   Actual columns map to locations; ACH columns are ignored.
4. Confirm four readings. Both files contain dates, so the dashboard for
   **2026-10-02** combines both divisions.
5. Select the off-target Network Availability reading at Demo North. Its uploaded
   feedback is available for a draft RCA.
6. Select Latency at Demo North to demonstrate the missing-feedback result.
   Enter division observations and a proposed action to produce a cited draft.
7. Change division/date filters and inspect history/source attribution.

The CSV samples are deliberately synthetic and can also be opened in Excel. Real
user-supplied reference workbooks are not bundled into demo assets or submitted to
a provider automatically.

## Interpretation boundaries

This is a competition prototype that can also be hosted as a public demo. Even when
deployed, it has no authentication, division verification or production deployment
controls. Division identity is selected by the user, not verified. Confirmation
records review of mappings; RCA drafts remain advisory and are not automatically
certified or executed. A citation check verifies source identity, not semantic truth.

Choose the header row/depth and worksheet explicitly for complex files. Excel
formula cells require cached values saved by Excel; the server does not calculate
arbitrary workbook formulas. Wide columns must represent actual measurements for
one location. Multiple location-specific targets should use row-format records.
New KPIs default to Performance unless a supported Category column is provided.
No automatic cross-workbook formula resolution, arbitrary report understanding,
incident prediction or causal discovery is claimed.

Duplicate readings are rejected rather than silently revised. Correct the source
before confirmation; a revision/replacement workflow is not implemented. Each
request validates at most 5,000 source rows/300 columns and imports up to 10,000
normalized readings. The ledger shows received reports; expected-division tracking
is not configured.

## Legacy seed and compatibility

The original seed generator remains available for synthetic history:

~~~powershell
cd backend
# Replaces the local database, including submissions; use only for a deliberate reset.
python seed_data.py
~~~

The dashboard separates **Division submissions** from **Synthetic seed history**.
Seed Z-scores retain their original static 29-point baseline unless that series is
subsequently recomputed by an import. Seed logs are not treated as division feedback.
The old /harvest preview endpoint and legacy FTS5 retrieval helper remain available
for historical experiments; the UI uses /submissions and feedback-based /rca.

## Verification

~~~powershell
cd backend
python -m unittest test_product_flow test_demo test_ai_revision -v
cd ../frontend
npm run lint
npm run build
~~~

Integration tests use an isolated temporary database and mock provider responses.
They cover multi-division imports, wide/multirow headers, Excel percentage scaling,
manual/AI mapping review, memory reuse, atomic validation, duplicate protection,
target direction, causal statistics, exact feedback scope and invalid citations.
`test_ai_revision.py` also checks the recorded-fallback label, the skipped state for
unknown layouts and the mapping-evaluation endpoint. These checks are not an industry
accuracy benchmark.

### Mapping benchmark and recorded suggestions

~~~powershell
cd backend
python benchmark_mapping.py --repeats 3                                   # local rules baseline
python benchmark_mapping.py --live-ai --repeats 3 --output evidence/mapping-benchmark-live.json
python record_ai_mappings.py                                              # refresh recorded suggestions
~~~

The live run writes one row per layout and repeat. In the committed run
(`evidence/mapping-benchmark-live.json`, `google/gemini-2.5-flash-lite`), local rules
scored 7/7 on conventional and Indonesian headers, 0/7 on unfamiliar and reordered
headers, and 9/9 on the wide layout. The provider reached 7/7 on the unfamiliar
layout and 6/7 on the reordered layout, with roughly 1.5–2 s per preview. Five
synthetic author-labelled layouts are not held-out real-report evidence.

The stack remains React/Vite, Tailwind CSS, Recharts, FastAPI, SQLAlchemy, SQLite,
openpyxl and an OpenAI-compatible model router. No model is trained from scratch.

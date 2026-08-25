# ANTIGRAVITY — ENGINEERING BUILD TIMELINE

Same two binding deadlines as Faizh's research track:
- **CALIBER registration close: 6 September 2026** (must be done before this)
- **CALIBER proposal submission: 4 October 2026, 23:59 WIB** (needs working mock-up/prototype + 3-min video + deck)
- **ITASE proposal submission: 17-18 October 2026** (proposal-focused, doesn't require a live demo, but reuses the same working prototype)

CALIBER is the tighter constraint — build order below is sequenced backward from Oct 4.

---

## STEP 0 — CALIBER Registration
**Deadline: 5 September 2026 (buffer before Sept 6 close)**
- Complete registration at https://chandra-asri.com/id/caliber, confirm Case 2 selection.
- Secure faculty advisor (dosen pembimbing) — required per T&C.

## STEP 1 — Database Schema + Seed Data Generator
**Deadline: 12 September 2026**
- `database.py`: Star Schema (`dim_kpi`, `dim_location`, `dim_period`, `dim_domain`, `fact_kpi`, `shift_logs`) per `ANTIGRAVITY_PROJECT_CONTEXT.md`.
- Recursive CTE rollup (leaf-node anchor via `NOT EXISTS`).
- Seed data generator (Python script): 30-day historical window per KPI+location for Z-score baseline, minimum 10 samples.
- **Expand seed KPI set to 15-20 KPIs per domain** (not just the original 10) — 10 total across 2 domains looks thin for a "90+ KPI" origin story when demoed.
- Populate the two Golden Flow demo scenarios (telco fiber cut, petrochemical pump trip) from `Demo_Case_Studies_OmniKPI.md`.

## STEP 2 — FastAPI Backend
**Deadline: 19 September 2026**
- `main.py`: `Depends()`-based domain_id isolation at router level.
- Anomaly detection endpoint (Z-score/IQR, `|Z| > 2.0`, min-sample guardrail).
- Harvester Agent: Excel ingestion, rapidfuzz column mapping + LLM fallback (<80% confidence).
- RCA data retrieval: SQLite FTS5 + SQL metadata filter on `shift_logs`.

## STEP 3 — React Frontend (Heatmap Dashboard)
**Deadline: 26 September 2026**
- Vite + TailwindCSS + Recharts SPA.
- Heatmap matrix rendering KPI status by location, color-coded by Z-score anomaly (not simple binary threshold).
- This frontend **doubles as the CALIBER mock-up/prototype deliverable** — build it navigable and presentable, not just functional.

## STEP 4 — RCA Agent Integration
**Deadline: 30 September 2026**
- Connect to LLM via OpenRouter/NineRouter free-tier.
- **Pick and document a specific model** (not just "whatever's free") — justify against: context window sufficient for shift log retrieval, instruction-following quality for structured JSON output, latency acceptable for interactive queries. Needed for ITASE's "alasan pemilihan teknologi" scoring criterion.
- RCA output format: root cause, confidence score (derived from Z-score, not LLM-generated), prescriptive action — matching JSON structure in `Demo_Case_Studies_OmniKPI.md`.
- Prepare a paid-provider fallback for the CALIBER Final Stage (24-hour live hackathon) in case free-tier hits rate limits on the day.

## STEP 5 — Video Demo Recording
**Deadline: 2 October 2026**
- Screen-record the actual running prototype (720p, H.265 compression) — doubles as proof-of-functionality and demo footage.
- English voiceover script, rehearsed not improvised.
- Combined package (mock-up + video + deck) must stay under 10MB total — plan compression budget accordingly (roughly 4-7MB left for video after deck).

## STEP 6 — CALIBER Submission Package
**Deadline: 3 October 2026 (buffer before 4 Oct 23:59 deadline)**
- Final assembly: mock-up/prototype link, video file, 7-slide PDF deck from Faizh.
- Verify all materials are in English.
- Verify combined size ≤ 10MB.

## STEP 7 — ITASE Supporting Materials
**Deadline: 10 October 2026**
- Flowchart diagram for BAB III (Excel Ingest → Star Schema DB → Z-Score Anomaly → LLM RCA) — visual asset for Faizh's proposal.
- Confirm the same working prototype supports ITASE's narrative without rework.

---

## RINGKASAN

| Step | Deadline |
|---|---|
| CALIBER registration + advisor | 5 Sep |
| Schema + seed data generator (15-20 KPI/domain) | 12 Sep |
| FastAPI backend + anomaly endpoint | 19 Sep |
| React heatmap frontend (= CALIBER mock-up) | 26 Sep |
| RCA Agent + model selection justified | 30 Sep |
| Video demo recording | 2 Oct |
| CALIBER submission package assembled | 3 Oct |
| ITASE supporting materials (flowchart, etc.) | 10 Oct |

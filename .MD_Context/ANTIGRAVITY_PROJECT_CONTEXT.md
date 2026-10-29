# OMNIKPI — CURRENT PRODUCT CONTEXT

## User-confirmed motivation

During a Performance & Support Network internship at Infranexia, the user's team
received KPI reports from divisions such as Mobile Broadband, Fiber Connectivity
and Core Network. The supervisor spent substantial effort collecting scattered
reports and compiling one Excel performance view for analysis and stakeholders.
RCA explanations came from division feedback, not an assumed shift-log pipeline.

The product now focuses on divisional Excel submissions becoming a unified
central dataset and performance view. Layouts can change but are usually stable,
so reviewed mappings can be reused. Keep scope appropriate for a competition
demonstration, rather than expanding into enterprise deployment or procurement.
Do not invent measured productivity or accuracy results.

## Implemented competition workflow

Upload .xlsx/.csv → propose/edit mappings → validate → confirm → consolidated
dashboard → obtain division feedback → advisory RCA draft with source references.

The Harvester supports tidy records and location columns, selected worksheet,
one to three header levels, explicit reporting dates, exact-layout mapping memory,
and optional LLM suggestions using headers and bounded sample values. No report
data is sent for AI mapping unless the upload checkbox is enabled.

Confirmation persists facts with division, filename and source-row attribution.
Missing values and incompatible definitions block import; duplicates do not
overwrite existing readings. No replacement/revision workflow is implemented.

Dashboard colors reflect target attainment using KPI direction and per-reading
targets. Statistical Z-scores are separate context, computed causally for imported
series from prior points in 30 calendar days (minimum ten). History shows up to
thirty readings and their applicable targets. Views filter by division and exact
report date; datasets separate imported reports from legacy synthetic seed data.

Division feedback is stored against the exact fact_id, which determines KPI,
location and date. With no feedback, the RCA endpoint returns Bukti Tidak Cukup
without an LLM call. Feedback-present drafts may use the configured provider and
must cite recognized feedback IDs. Provider errors or invalid citations fall back
to verbatim attributed feedback. Citation validity is not proof of causal truth.
The old confidence percentage is not part of this endpoint or UI.

Two synthetic CSV samples in frontend/public/demo demonstrate six Mobile Broadband
readings and four Fiber Connectivity readings, unified on 2026-10-02. Do not copy
user-provided company workbooks into public demo assets.

## Architecture and limits

React/Vite SPA + Tailwind/Recharts; FastAPI; SQLAlchemy/SQLite. Domain 1 is telco.
New tables: submissions (local staged JSON and confirmed ledger), reading_sources,
mapping_memory and division_feedback. Existing facts and local DB are preserved.
Startup creates missing tables and a telco domain; the seed command remains a
deliberate destructive reset, not an upgrade step.

The prototype has no authentication. Division identity and feedback authorship
are not verified. No network-control integration, causal-discovery model, prediction,
arbitrary Excel formula evaluation or universal ingestion capability is claimed.
Complicated templates may need manual header selection/mapping or conversion to
rows, especially for location-specific targets. New categories must be supplied
or use the disclosed default Performance grouping.

The legacy Harvester route and log-retrieval helper remain for old experiments.
The main UI uses the new intake endpoints and feedback-based RCA. Legacy seed
statistics are historical artifacts and do not prove the new workflow's accuracy.

## Competition context

One telco product targets ITASE 7.0 and the UiPath–Indosat Automation Hackathon.
UiPath is not integrated yet; the hackathon requires it to be the core automation.
Do not describe this prototype as already meeting that requirement.

The Documents folder contains the submitted 31-page proposal, guidebook and
event-day images. Preserve these historical source files. Latest ITASE images:
deck deadline 6 November 2026 23:59 WIB, PDF/PPTX; online final 7 November;
ten minutes presentation plus ten minutes Q&A. Required deck content: cover,
problem, solution innovation, AI use, design/workflow, feasibility, SDGs, conclusion.
Final rubric: deck completeness 20%, presentation 50%, Q&A 30%.

Automation Hackathon: submission 25 November 2026 23:59 WIB, PPTX + source ZIP +
MP4 (maximum 100 MB); final showcase 7 December. Final materials must match the
submitted version. Both competitions use pretrained AI; no custom training is
needed for the current product.

## Verification

backend/test_product_flow.py exercises isolated DB workflows and mocked provider
outputs, not empirical industry accuracy. Keep claims about API integration,
sample demos and provider validation distinct. The proposal's E1–E4 benchmarks,
incident grouping and broader roadmap are not completed by these smoke checks.

# Product brief

## Origin and user

The project grew from the user's Performance & Support Network internship at Infranexia. The team handled KPI submissions from groups such as Mobile Broadband, Fiber Connectivity and Core Network. The supervisor's concern was that divisional data arrived scattered across files; she manually combined Excel extracts into a common view before reviewing performance and reporting to stakeholders.

The primary user in the presentation is a performance analyst who receives recurring files from multiple divisions. Division representatives remain responsible for the measurements and for explaining a shortfall. Stakeholders need an understandable consolidated view.

This is the user's account of the work setting, not a claim that Infranexia endorsed or deployed omniKPI. Do not use confidential reports or imply that synthetic examples are company results.

## The problem to make concrete

The costly handoff happens before the analysis: reports are stored separately, layouts and labels must be reconciled, and the analyst assembles a cross-division workbook. This creates repetitive preparation work and makes it harder to keep each reading connected to its submitting unit and source row.

The product addresses this reporting workflow. It does not claim that all telco data is unstructured, that every operator has the same reporting structure, or that reporting consolidation itself proves a network root cause.

## Product promise

Submit a divisional report, review how its columns were interpreted, confirm valid readings, and view the combined KPI dataset with provenance. Target checks make missed thresholds visible. Division feedback can be attached to the exact KPI, location and date for an attributed RCA draft.

## What is innovative here

The product idea combines a shared, traceable divisional KPI dataset with AI assistance at the point where report layouts need interpretation. Rather than presenting an LLM chat panel as the product, omniKPI places AI inside the report intake and explanation steps:

- Schema interpretation proposes what report columns mean from their headers and a small number of sample values. The analyst reviews the mapping before data is confirmed.
- Evidence-linked RCA can turn feedback already attached to a specific reading into an attributed draft. It must not treat the KPI deviation alone as proof of cause.

The central workflow and source traceability are product capabilities. AI assists with interpretation and language; deterministic code handles validation, duplicate checks, target status and statistical calculations. Do not say AI performs the consolidation or discovers causality.

## Story arc

1. An analyst receives separate division submissions.
2. Manual compilation consumes effort and separates readings from their context.
3. omniKPI stages each report, proposes a schema mapping, and asks the analyst to review it.
4. Confirmed readings enter a shared view while retaining unit, file and row provenance.
5. A missed target prompts a request for division feedback; omniKPI drafts an attributed explanation for analyst review.
6. The competition demo uses reconstructed synthetic files to show this workflow without exposing company data.

## Keep the scope credible

Present omniKPI as a competition prototype and a concrete direction for improving divisional reporting. A production shared data lake, automatic division identity, enterprise authentication, deployment integration and verified operational impact are future implementation work, not current claims.

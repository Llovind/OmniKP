# Current system and demo facts

## Implemented workflow

`Upload report -> map columns -> review and validate -> confirm -> shared dashboard -> attach division feedback -> request an RCA draft`

### Intake and mapping

- FastAPI accepts Excel and UTF-8 CSV reports. Intake supports a selected worksheet, a selected header row, and one to three header levels.
- Local aliases and fuzzy matching produce baseline mapping suggestions. An optional pretrained LLM can use headers plus up to three sample values per column. Provider use is opt-in during upload.
- Every AI proposal carries a short reason. Each preview response also returns a trace of what actually happened: mode (`live`, `recorded`, `skipped`), model, provider, column count, sample limit, batches, fallback batches and latency. No confidence percentage is produced.
- When no provider key is configured, the seven demo header signatures replay recorded provider output. The interface labels it “AI suggestion · recorded” and the response states that it is not a live call. Unknown layouts return the skipped state instead of inventing suggestions.
- `GET /api/v1/ai/status` reports the configured mode and model. `GET /api/v1/ai/evaluation` and the `/evaluation` page publish the synthetic five-layout comparison of local rules versus the provider.
- The analyst reviews and can correct the proposed mapping. Confirmed mappings can be reused for the same division and exact ordered header signature.
- Validation blocks invalid or duplicate readings before confirmation. Confirmed records retain submitting division, filename and source row.

### Dashboard and analysis

- The dashboard combines imported KPI readings and can filter by reporting date and division. It shows source attribution and a submission ledger.
- Target attainment is computed from actual, target and higher/lower-is-better direction. Target status is deterministic.
- Imported statistical history uses prior readings in a 30-calendar-day window, with a minimum of ten prior points. A statistical anomaly is separate from target attainment. Do not describe this as a trained anomaly-classification model or forecasting.
- Division feedback is linked to an exact reading, which determines KPI, location and date. Without feedback, the RCA endpoint returns an insufficient-evidence response without calling an LLM.
- When feedback exists, an optional configured model may draft an attributed explanation. The server checks feedback IDs and inline citations. If the provider fails or returns invalid citations, an attributed feedback summary is used. Citation validity confirms source identity, not that the explanation is true.
- RCA responses state whether the model was invoked and report how many claims lacked a feedback reference. The structural check is not a semantic proof.
- RCA actions are advisory. The system does not execute network changes.

## Stack

- Frontend: React and Vite, with Tailwind and Recharts.
- Backend: FastAPI, SQLAlchemy and SQLite.
- Optional AI: pretrained model through an OpenAI-compatible router; no model is trained from scratch.

## Synthetic divisional demo

The one-click demo loads seven reconstructed Excel reports through the existing intake and confirmation services into an isolated synthetic database. The validation pack also includes a separately calculated reference workbook and machine-readable expected readings.

| Submitting unit | KPIs | Readings |
|---|---:|---:|
| BGES & OLO | 41 | 82 |
| MBB | 17 | 34 |
| ED | 13 | 26 |
| NETOP OSP | 8 | 16 |
| FBB | 8 | 16 |
| AIM | 2 | 4 |
| DEFA | 1 | 2 |
| Total | 90 | 180 |

The demo date is 2026-06-30. It contains two fictional locations, Demo North and Demo South. The reference outcome is 121 readings meeting target and 59 missing target.

KPI names, units, directions and submitting-unit grouping follow the structure of the June WISA reference workbook. The demo's actual values, targets, locations and feedback are synthetic. These files are reconstructed demo inputs, not recovered division templates or original Infranexia reports. The original consolidated workbook is not treated as a single division's upload.

## What the demo verifies

The import integration test checks the seven fixtures against expected readings, targets, units, dates, status, location, unit ownership, filters and ledger totals. The expected workbook is independently calculated from exported fixture cells rather than from the app's intake, mapping or target-status helpers. This reduces shared-implementation errors. It is not third-party certification, a held-out AI benchmark, or proof of real-world mapping accuracy or time savings.

### Synthetic mapping benchmark (measured 6 November 2026)

`backend/evidence/mapping-benchmark-live.json` records three repeats per layout with
`google/gemini-2.5-flash-lite` through an OpenAI-compatible router.

| Layout | Local rules | Provider + review | Provider latency |
|---|---:|---:|---:|
| standard | 7/7 | 7/7 | ~1.5 s |
| indonesian | 7/7 | 7/7 | ~1.6 s |
| unfamiliar | 0/7 | 7/7 | ~1.7 s |
| reordered | 0/7 | 6/7 | ~1.6 s |
| wide with achievement | 9/9 | 9/9 | ~1.9 s |

State it as: on five author-labelled synthetic layouts, the provider recovered
unfamiliar and reordered headers that local rules could not map, while adding
roughly 1.5–2 s per preview. One reordered column (“Reporting area”) remained
unmapped. This is not held-out real-report accuracy, not analyst time saved, and not
independent validation. The two unfamiliar layouts share vocabulary.

Three separate files exercise failure cases: a missing value, a duplicate reading and changed headers. They are validation exercises, not successful division submissions.

## Submitted proposal versus the current prototype

The submitted 2026 proposal is broader than the product now being prepared for the ITASE final. It described a cross-industry concept with shift-log retrieval, a statistical heatmap, incident grouping across KPIs, an Isolation Forest second signal, hybrid BM25 plus embeddings, citation checks, a Case Library, recovery verification and six facility-level SDG indicators. The proposal's own implementation-status table marked several of these as planned or not yet implemented at that time.

The current telco demo has since concentrated on the divisional-report pain point: accepted spreadsheet intake, analyst-reviewed mapping and validation, confirmed consolidation with source attribution, target status, and feedback-linked RCA drafts. Do not carry the proposal's broader module list into a “built today” diagram. If a judge compares the deck with the submitted proposal, explain this as a scope refinement from the broader concept into a runnable, testable divisional reporting workflow.

The proposal's economic sensitivity examples, early mapping observations and proposed evaluation targets are not measured results from the current demo. Do not use them as achieved outcomes or current benchmark scores.

## Limits to state plainly

- No production deployment, authentication or verification of division identity. A hosted demo URL may exist; treat it as a prototype deployment without production controls.
- Recorded AI suggestions are replayed provider output, not live inference. They exist so the demo survives a missing key or provider outage and are always labelled.
- The synthetic benchmark is five authored layouts with a single model family; it is not a held-out or real-report evaluation.
- No evidence of measured productivity, human time saved, operational accuracy, outage reduction or financial impact.
- No custom-trained model, forecasting, causal discovery or automatic remediation.
- Complex layouts may need manual header selection or mapping; formula evaluation and arbitrary report understanding are not claimed.
- RCA is based on supplied division feedback. The model can still phrase a reported explanation poorly; human review remains necessary.
- The demo locations and targets are fictional and should not be presented as operator geography or SLAs.

## Useful repo references

- `README.md`: setup, current product behavior and limits.
- `backend/routers/demo.py`: isolated one-click demo seed.
- `backend/services/intake.py`: parsing, mapping, review, validation and confirmation.
- `backend/services/performance.py`: deterministic target status and history recomputation.
- `backend/agents/feedback_rca.py`: feedback-scoped RCA and fallback behavior.
- `backend/evidence/division-demo/README.md`: fixture provenance and walkthrough.
- `frontend/public/demo/divisions/VALIDATE.md`: reference comparison instructions.

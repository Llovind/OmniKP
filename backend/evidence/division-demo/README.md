# Seven-unit consolidation demo

Source: `KPI_data/KPI WISA FM JUNI  2026.xlsx`, sheet `WISA REKON BARU`, rows 4–93. Submitting units follow column L, `SUB-UNIT REG BARU`, trimmed of trailing whitespace. This is one regional sub-unit grouping, not an assertion that every workbook uses the same organization chart. Column G's UIC-TIF and the older ownership mapping are different dimensions and are not substituted for this grouping.

| Unit | KPIs | Synthetic readings |
|---|---:|---:|
| BGES & OLO | 41 | 82 |
| MBB | 17 | 34 |
| ED | 13 | 26 |
| NETOP OSP | 8 | 16 |
| FBB | 8 | 16 |
| AIM | 2 | 4 |
| DEFA | 1 | 2 |

KPI names, units and higher/lower direction are retained from the source, including percentage compliance measures whose names mention latency or jitter. Do not reinterpret those as raw milliseconds. Measurements, targets, feedback and two locations are synthetic. The reconstructed flat/wide layouts are designed demo inputs, not recovered original divisional templates. Source performance readings and source targets are never copied.

## Walkthrough

Open Upload report. Under Division demo workbooks, choose Load for each unit. The file, date (2026-06-30), sheet (Report), and header row (4) are populated. Interpret, review, validate and confirm each one. AI is optional; the known source headers also work with local rules. Downloads are available beside each Load button.

After all seven imports, select Division submissions, All divisions, 2026-06-30: expect 180 readings, 90 distinct KPIs, two demo locations and seven report entries. Filter by unit to see the counts above. Off-target rows in the row-layout reports include explicitly synthetic division feedback for the RCA demonstration. Wide-layout reports intentionally lack feedback, allowing the insufficient-evidence path to be demonstrated. Repeat imports are rejected.

The original consolidated workbook is not accepted as a single-unit input: it has multiple owners, reference tables, missing readings and local-target variations. Removing an AI column cap alone cannot solve those semantics. The upload endpoint explains this and directs users to the reconstructed files. Wide supported inputs are interpreted in batches of 60 columns, up to the existing 300-column parser limit, with per-batch fallback and mandatory review.

## Verification

`python -m unittest test_product_flow -v` imports every delivered XLSX through the real endpoints into a temporary database and checks all 180 actuals, targets, units, dates, statuses, location and unit ownership, plus filters and ledger totals. This is reconstruction correctness, not a held-out AI-accuracy benchmark. No human time savings are inferred.

Rebuild definitions with `python build_division_demo.py`, then workbooks with `node render_division_demo.mjs` using the artifact-tool runtime. `ownership.json` records source row provenance; `expected.json` is the reconciliation reference.

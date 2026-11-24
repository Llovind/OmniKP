# Expected outputs

Reporting date `2026-06-30`. All inputs and findings are synthetic.

| Division | Workbook | KPIs | Readings | Meeting target | Below target |
| --- | --- | ---: | ---: | ---: | ---: |
| ED | `ed.xlsx` | 13 | 26 | 17 | 9 |
| BGES & OLO | `bges-olo.xlsx` | 41 | 82 | 55 | 27 |
| NETOP OSP | `netop-osp.xlsx` | 8 | 16 | 11 | 5 |
| AIM | `aim.xlsx` | 2 | 4 | 3 | 1 |
| FBB | `fbb.xlsx` | 8 | 16 | 11 | 5 |
| MBB | `mbb.xlsx` | 17 | 34 | 23 | 11 |
| DEFA | `defa.xlsx` | 1 | 2 | 1 | 1 |
| **Total** | **7 files** | **90** | **180** | **121** | **59** |

Demo North and Demo South are the two locations. Compare each reading with `Expected readings` in the [independent workbook](../../frontend/public/demo/divisions/expected-consolidated.xlsx). The fixture package also supplies [expected readings as JSON](../../frontend/public/demo/divisions/expected-readings.json) and [workbook checksums](../../frontend/public/demo/divisions/validation-summary.json).

| Artifact | Expected content |
| --- | --- |
| `Logs/<run>/baseline.json` | Exact disposable identity, empty periods and confirmed ledger at the start |
| `Logs/<run>/run-manifest.json` | Folder and workbook statuses, SHA-256 input fingerprints and current human review step |
| `Logs/<run>/<division>/<sha256>/` | Preview intent and live AI response, mapping attempts, import authorization and reconciled confirmed detail |
| `Output/<run>/<bundle>/<revision>/aggregate-bundle.json` | Backend snapshot, 180 readings with exact source rows, shortfalls, divisions, locations, submissions, feedback and narrative state |
| `reconciliation.json` | Fixture comparison and backend detail, heatmap and anomaly agreement |
| `narrative-request.json` and `narrative-decision.json` | Bundle and template fingerprints and the explicit scoped decision |
| `report/VantageNet-<bundle>-<revision>.pptx` | Seven editable slides with the approved narrative, counts, references and submission provenance |
| `report/generation-receipt.json` | SHA-256 hashes for the report and decision, request hash and approval mode |
| `report/report-proof.pdf` | Optional proof opened and rendered by PowerPoint |

If a division is missing, rejected or unresolved, the run manifest identifies it and the final report is blocked. The exact AI wording and backend IDs vary by run. Provider errors are preserved for diagnosis and require another report revision. The automated acceptance outputs display their test decision mode.

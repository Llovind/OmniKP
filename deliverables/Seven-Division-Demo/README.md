# VantageNet seven-division automation demo

The attended UiPath robot collects the seven synthetic division workbooks from configurable folders, sends each to the existing live AI mapping API, and pauses twice per workbook. An operator first reviews or corrects the mapping. After backend validation, the operator separately authorizes the import. The robot reconciles each confirmation using the submission ledger before moving on.

VantageNet captures the full reporting date from the disposable database. The robot reconciles that snapshot against the confirmed submissions, dashboard heatmap, shortfalls API, and the synthetic reference. After explicit narrative approval, a separate UiPath workflow fills an editable seven-slide management PowerPoint.

- [Runbook](RUNBOOK.md)
- [Expected outputs](EXPECTED_OUTPUTS.md)
- [Test evidence](TEST_EVIDENCE.md)
- [Initial implementation plan](../../automation/uipath/VantageNet.Reporting/SEVEN_DIVISION_PLAN.md)

## Source changes

| Area | Files |
| --- | --- |
| UiPath orchestration and report | `RunSevenDivisionDemo.cs`, `SevenDivisionRun.cs`, `SevenDivisionReport.cs`, `GenerateSevenDivisionPptx.cs`, `project.json` |
| Local launcher and review assets | `Start-SevenDivisionDemo.ps1`, `Data/seven-division-review.html`, `Data/seven-division-template.pptx` |
| Backend | `routers/submissions.py`, `services/intake.py`, `services/aggregate_report.py`, `routers/anomaly.py`, `services/performance.py` |
| Verification and template build | `Tests/test_seven_division_demo.py`, `Tests/verify_seven_division_report.py`, `Tests/New-SevenDivisionTemplate.ps1` |
| Documentation and evidence | This directory, `SEVEN_DIVISION_PLAN.md`, and the UiPath project `README.md` |

## Integration boundaries

- The input adapter uses Windows folders. A hydrated OneDrive sync root works as the same filesystem input. Microsoft Graph and Action Center are outside this implementation.
- Decisions are local browser downloads consumed by UiPath. The reviewer types their name. The JSON and hash bindings tie decisions to a specific request and provide local traceability. The review mechanism assumes a trusted workstation and does not authenticate the reviewer or enforce authorization on direct backend calls.
- Inputs and expected results are synthetic. Worksheet notes retain their fixture origin. The backend drafts RCA for one below-target reading with exact-fact evidence and retains all shortfalls and feedback in the bundle. Gaps without feedback have insufficient evidence for a causal claim.
- The demo uses a loopback FastAPI backend and a new disposable SQLite database. Delivery is local PowerPoint generation. Notifications, deployment, production identity management, and automatic reporting schedules are outside scope.

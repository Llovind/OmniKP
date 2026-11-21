# VantageNet attended ED demo

Use the public synthetic ED workbook for one division, one period, and one selected KPI shortfall. The backend owns the reading and its evidence. The analyst approves the mapping and the final wording. UiPath runs the import and creates the local report.

The [synthetic dataset folder](../frontend/public/demo/divisions) contains [ED](../frontend/public/demo/divisions/ed.xlsx) and six other division workbooks. The [manifest](../frontend/public/demo/divisions/manifest.json) lists the sheet, header layout and reporting date for each input. The [expected consolidated workbook](../frontend/public/demo/divisions/expected-consolidated.xlsx) is a reference output. This attended robot confirms only ED. Cross-division aggregation can be demonstrated in the app's synthetic demo.

## Prepare the demo machine

1. On Windows, install the backend requirements from `backend/requirements.txt` in a virtual environment. Configure the approved AI provider locally using `backend/.env.example` as a reference.
2. Open `automation/uipath/VantageNet.Reporting/project.json` in compatible UiPath Studio Desktop. Restore, validate, and build the project. See the [UiPath README](../automation/uipath/VantageNet.Reporting/README.md) for the tested environment and CLI commands.
3. From `backend/`, run the following in PowerShell with the backend environment active. The random instance name creates a fresh database for the run.

```powershell
$instance = 'ed-demo-' + [guid]::NewGuid().ToString('N')
$db = Join-Path ([IO.Path]::GetTempPath()) "$instance.db"
$env:DATABASE_URL = 'sqlite:///' + $db.Replace('\', '/')
$env:VANTAGENET_DISPOSABLE = '1'
$env:VANTAGENET_DISPOSABLE_INSTANCE_ID = $instance
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/_development/instance` before import. It should return `disposable: true`, domain 1, and the instance ID from the command above.

## Run the attended workflow

| Step | UiPath entry point and inputs | Expected evidence |
| --- | --- | --- |
| 1. Preview | `Main.xaml` with `in_ConfigPath` set to the absolute path of `Data/config.example.json` | `manifest.json` and `mapping-review.html`. Open the form and check the AI proposal. |
| 2. Review | `ReviewMapping.cs` with `manifestPath`, `baseUrl=http://127.0.0.1:8000` and the downloaded `decisionPath` | Submit a correction if the proposal needs one. If all suggestions are correct, show the analyst reviewing them and accepting them as supplied. The validated mapping must produce 26 readings. |
| 3. Confirm | Run `ReviewMapping.cs` again without a decision to prepare the approval form. Save a fresh approval with explicit import authorization and the displayed instance ID. Validate that approval with `ReviewMapping.cs`, then pass it as `approvalPath` to `ConfirmSubmission.cs` with the same manifest and base URL. | `confirm-journal.json` shows `verified_confirmed`. `confirm-ledger.json` contains 26 readings with source rows. If a confirm times out, retain the journal and reconcile using the same run. |
| 4. Draft | Find the RED reading at worksheet row 5 in the confirmed ledger. Run `FetchReportBundle.cs` with the manifest and that reading's `factId`. Pass its returned bundle path to `AdaptReportBundle.cs` as `bundlePath`, along with `expectedInstanceId`. | A staged v2 snapshot for the exact reading and a `draft_ready` status. Blocked evidence statuses produce no review snapshot. |
| 5. Approve | Run `ReviewNarrative.cs` with the staged `snapshot.json` and `Data/provisional-report-template.pptx`. Read the evidence, edit the draft if needed, and save the decision in the form. Run the same workflow again with `decisionPath`. | A review request and a saved decision tied to the run, snapshot, and template. |
| 6. Generate | Run `GenerateNarrativePptx.cs` with the review folder's `request.json` and the approved decision file. | A local PPTX and generation receipt. Open the slides and compare the KPI, location, source row, cited feedback, and approved wording with the saved run evidence. |

The row 5 reading is **Demo North**, with an actual of **97.8%** and a target of **98.5%**. The evidence starts as a synthetic worksheet note. Identify it that way in the video. A new bundle revision needs a fresh narrative decision.

## Acceptance and recording

- In a separate fresh run, reject the mapping and check that no readings were added for that submission.
- Verify that an old narrative decision cannot generate a report from a changed revision.
- Ask a teammate to repeat the main run using this guide. Save the selected reading, decision records and report receipt as internal evidence. Show the real review screens and finished report in the video.
- Use the pitch deck, source ZIP, and demo MP4 as separate submission artifacts. The project brief records a 100 MB video limit. [Project submission checklist](VANTAGENET.md#11-definition-of-done-dan-submission)

## Verification so far

The disposable backend smoke test confirmed 26 ED readings and produced a schema v2 draft for source row 5 through the live AI provider. The backend verified the citation and classified the feedback as a worksheet fixture. The smoke test used a programmatic mapping decision. The UiPath build, attended decisions, generated report, and recording require the demo-machine run above.

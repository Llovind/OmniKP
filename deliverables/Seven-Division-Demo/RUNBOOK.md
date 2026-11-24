# Run the seven-division demo

## 1. Prepare the workstation

Use Windows with the installed UiPath CLI, the project’s existing package cache and the `vantagenet-local-noauth` profile, an existing Python environment with `backend/requirements.txt`, Node and npm, a browser, and desktop PowerPoint for opening the report. Run the commands from the repository root in PowerShell. Adjust only the installed executable paths where necessary.

```powershell
$p = Join-Path $PWD 'automation/uipath/VantageNet.Reporting'
$uip = 'C:/Program Files/UiPathPlatform/Studio/26.10.0-cloud.25715/cli/uip.cmd'
$python = "$env:LOCALAPPDATA/VantageNet/acceptance-venv/Scripts/python.exe"
$env:UIPATH_CLI_DISABLE_AUTOINSTALL = 'true'
$env:UIPATH_CLI_DISABLE_VERSION_SYNC = 'true'
Push-Location frontend
npm.cmd ci --no-audit --no-fund
npm.cmd run build
Pop-Location
& $uip rpa build $p --profile vantagenet-local-noauth --governance-file-type Default --output json
```

Start the configured live AI provider. For the installed Ollama configuration, use the local AI section of the [existing runbook](../Gate-3D.1-VantageNet/RUNBOOK.md) to run and warm `qwen3.5:9b`. In the backend terminal set these process-scoped Ollama settings. For OpenRouter, use the secure key entry method in the existing runbook and set the endpoint and model for that provider.

```powershell
$env:OPENROUTER_BASE_URL = 'http://127.0.0.1:11434/v1'
$env:OPENROUTER_API_KEY = 'ollama-local'
$env:LLM_MODEL = 'qwen3.5:9b'
$env:OPENROUTER_MAX_RETRIES = '0'
```

## 2. Create the disposable workspace

Choose unused run and bundle identifiers and a new revision. Keep the backend terminal running. The launcher copies the seven fixture files into `Input` and initializes empty database tables. Supply `-InputRoot 'D:/path/to/synced/VantageNetDemo/Input'` to scan an existing hydrated folder instead. The names of the seven subfolders come from the manifest `folder` value, or the uppercase fixture filename stem when it is omitted.

```powershell
$run = 'seven-recording-01'
$bundle = 'seven-management-recording-01'
$revision = 'v10'
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$p/Start-SevenDivisionDemo.ps1" `
  -RunId $run -BundleId $bundle -Revision $revision -Port 8189 -Python $python
```

In a second terminal, set `$p`, `$uip`, `$python`, `$run`, `$bundle`, and `$revision` to the same values. Verify the exact `instance_id`, `database` and `disposable` fields before opening the dashboard. The first two lists should be empty before the robot starts.

```powershell
$origin = 'http://127.0.0.1:8189'
$root = Join-Path $PWD "tmp/$run"
$cfg = Join-Path $root 'seven-division-config.json'
Invoke-RestMethod "$origin/_development/instance"
Invoke-RestMethod "$origin/api/v1/domains/1/submissions"
Invoke-RestMethod "$origin/api/v1/domains/1/periods?dataset=all"
Invoke-RestMethod "$origin/api/v1/ai/status" | Select-Object configured,mode,model
```

## 3. Collect, review and confirm

Open the `Input` folder in Explorer. Run `Invoke-VantageBatch` with no decision to scan all seven folders. Open the returned `Output` path if it ends in `.html`. The CLI emits the path inside `Data.output`. The same workflows can be run from UiPath Studio with the same arguments.

```powershell
function Invoke-VantageBatch([string]$DecisionPath) {
  $arguments = @('rpa','run','--file-path','RunSevenDivisionDemo.cs','--project-dir',$p,
    '--profile','vantagenet-local-noauth','--skip-build','--output','json',
    '--input-arguments',"projectFolder=$p",'--input-arguments',"configPath=$cfg")
  if ($DecisionPath) { $arguments += @('--input-arguments',"decisionPath=$DecisionPath") }
  & $uip @arguments
}
Invoke-VantageBatch
```

1. On **Review column meanings**, inspect the AI proposal against the worksheet samples. `REAL` columns contain readings. Map a wide actual column to `location:Demo North` or `location:Demo South`. Ignore the `ACH` columns. Approve the reviewed mapping for validation or reject it. Enter your own name and reason, then download the decision.
2. Resume with `Invoke-VantageBatch 'C:/path/to/downloaded/decision-mapping-ed.json'`, using the actual saved path. If validation finds a problem, open the new mapping form and correct or reject the mapping. Green status on the worksheet does not substitute for backend validation.
3. On **Authorize import**, review the validated mapping and count. Choose **Approve**, check the separate authorization box and download the import decision. Resume with its saved path. The robot verifies the resulting ledger and advances to the next submission. Repeat for all seven divisions.
4. Review `Logs/<run>/run-manifest.json` to see the source fingerprints and each division’s status. Once complete, reload `http://127.0.0.1:8189/app` and select **2026-06-30** and **All divisions**. Use the normal application URL throughout the recording. The alternate one-click demo prepares a separate fixture dataset.

## 4. Approve the narrative and generate

The returned `narrative-review.html` shows the reconciled totals, the exact reading in focus, feedback origin, and available RCA and recommendations. Choose **Approve** or **Reject** and submit the downloaded decision with `Invoke-VantageBatch`. Approval covers the displayed draft as written. A rejected bundle requires a new report revision and fresh review. Then run:

```powershell
& $uip rpa run --file-path GenerateSevenDivisionPptx.cs --project-dir $p `
  --profile vantagenet-local-noauth --skip-build --output json `
  --input-arguments "projectFolder=$p" --input-arguments "configPath=$cfg"

$reportRoot = Join-Path $root "Output/$run/$bundle/$revision"
& $python "$p/Tests/verify_seven_division_report.py" $reportRoot `
  'frontend/public/demo/divisions/expected-consolidated.xlsx'

$pptx = Join-Path $reportRoot "report/VantageNet-$bundle-$revision.pptx"
$pdf = Join-Path $reportRoot 'report/report-proof.pdf'
& $uip rpa run --file-path RenderReportProof.cs --project-dir $p `
  --profile vantagenet-local-noauth --skip-build --output json `
  --input-arguments "pptxPath=$pptx" --input-arguments "pdfPath=$pdf"
```

Open the PPTX in PowerPoint and inspect the seven slides. Use the actual recorded reviewer name and approved draft when capturing the silent demo.

## 5. Recover the run

| Condition | Operator action |
| --- | --- |
| Missing file, unsynced file or missing division folder | Restore the expected workbook and run the same robot command again. Keep the original configuration. |
| Extra XLSX or duplicate bytes | Inspect `run-manifest.json`. The manifest selects one expected workbook per division and skips extras. It blocks duplicate bytes across divisions. |
| Malformed workbook returns HTTP 422 | Check `preview-error.json` and `preview-reconciliation.json`. Replace it with the correct workbook if the ledger confirms it never staged, then resume. |
| Rejected mapping or invalid data | A rejection is terminal for those exact bytes. Correct the source upstream and resume with a replacement workbook or use a new disposable run. A partial batch produces no final report. |
| Preview outcome unknown | Inspect the client-assigned ID and `preview-reconciliation.json`. The robot does not repeat the POST automatically. If committed but its AI proposal was lost, preserve that draft and use a new disposable run for another attempt. |
| Confirmation outcome unknown | Resume with no decision. The robot reads the exact ledger entry and continues only if the stored confirmation matches the approved mapping and source. An unresolved draft remains blocked pending operator reconciliation. |
| AI error during aggregate capture or narrative rejection | Preserve the revision. Copy the config within the same workspace and change `bundle_id` and `revision` to new values. Point `$cfg` to that copy and resume with no decision. The robot reuses the reconciled imports and captures a new report request. |
| Backend stopped | Restart the launcher with the original IDs and `-Resume` against the original database, then resume the robot. |

## 6. Record the silent demo

| Shot | On-screen evidence |
| --- | --- |
| 1. Division folders | Explorer shows `Input` and the seven named folders. Open ED and one wide-layout workbook. |
| 2. Robot collection | Run `Invoke-VantageBatch`. Show the manifest with all known folders and workbook hashes. |
| 3. Human controls | Show the live mapping, one reviewed edit if needed, validation count and separate import authorization. Cut to the final division entering the ledger. |
| 4. Consolidated dashboard | Refresh the normal `/app` view. Show **All divisions**, `2026-06-30`, 90 KPIs and two locations. Open a below-target reading and show its workbook and source row. |
| 5. Narrative review | Show the cited fixture evidence, the insufficient-evidence scope and the analyst’s explicit approval. |
| 6. Management report | Run the report workflow and open PowerPoint. Show the `121` / `59` split, divisional performance and the provenance slide. |

Before recording, run a supervised rehearsal on a new workspace, mute capture audio, and stage Explorer, UiPath, browser and PowerPoint windows. Keep downloads and local paths outside the recording area when they reveal personal data. Do not record provider configuration or tokens.

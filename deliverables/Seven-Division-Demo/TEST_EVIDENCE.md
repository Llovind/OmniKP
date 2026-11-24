# Acceptance evidence

The tests ran on 24 November 2026 using the installed Windows UiPath CLI (`26.10.0-cloud.25715`), local FastAPI, Ollama `qwen3.5:9b`, and desktop PowerPoint. The harness used explicitly labeled automated decisions. The seven previews and the cited RCA came from the live backend and provider.

- [Machine-readable acceptance summary](evidence/acceptance.json)
- [Reconciled aggregate bundle](evidence/aggregate-bundle.json) and [reconciliation receipt](evidence/reconciliation.json)
- [Generated PowerPoint](evidence/report/VantageNet-seven-management-20261124a-v10-v10.pptx), [PowerPoint-rendered PDF](evidence/report/report-proof.pdf), and [generation receipt](evidence/report/generation-receipt.json)

## Observed results

| Exercise | Result |
| --- | --- |
| Clean start | Verified disposable instance `seven-live-20261124a`, database `sqlite:disposable-seven-live-20261124a.db`, empty periods and confirmed ledger. |
| Collection and import | Detected all seven folders. Fingerprinted seven XLSX files, obtained seven live AI mapping responses, and confirmed seven distinct submissions. |
| Independent reconciliation | Matched all 180 rows in `expected-consolidated.xlsx`, covering values, units, direction, attainment, status, source workbook, source row, date and division. Confirmed 90 KPIs, two locations, 121 meeting target and 59 below target. |
| Approval and replay | A mapping approval alone left the workbook in draft. Missing import authorization was rejected. A simulated loss of the local ED confirmation response recovered from the already committed ledger entry. Replaying the run introduced no extra readings. |
| Negative run | In `seven-negative-20261124a`, blocked missing values and duplicate readings inside workbooks, handled a malformed XLSX with HTTP 422, reported a missing division folder and a missing workbook, and skipped duplicate workbook bytes. Rejections left zero confirmed submissions and zero readings. |
| Narrative controls | The first generation attempt without a decision and a stale approval were blocked. A separate rejected narrative revision produced zero PPTXs and left all seven submissions unchanged. Report generation replay returned the same report hash. |
| RCA provenance | The live model produced a cited draft for NETOP OSP, Demo North. The cited evidence was synthetic worksheet feedback `[F6]`. Twelve of 59 shortfalls had worksheet feedback. |
| Browser | Viewed the local import authorization form and its validated count. The normal `/app` showed the confirmed totals and traced ED Demo North compliance to `ed.xlsx`, row 5. |
| PowerPoint | The final sample is revised output `v10`, generated from the same verified submissions. PowerPoint opened it, exported seven PDF pages and seven slide previews, and detected no out-of-bounds text. |
| Regressions | Installed UiPath build and production frontend build passed. All 26 `test_product_flow` tests and all six `test_ai_revision` tests passed. The six published Gate 3D.1 checksums still match. |

The initial generated revision exposed a template formatting issue in PowerPoint. Its files remain in the local test workspace. The delivered sample is `v10`, which preserves the template’s font sizes and colors and passed visual review. The report and PDF use synthetic data and are labeled as automated test output.

## Reproduce the checks

From the repository root, set `$p`, `$uip` and `$python` using the [runbook](RUNBOOK.md). Start the launcher on a fresh run with `-AutomatedTest` and a warmed live provider. Supply the config path it prints to the automated script. The harness deliberately submits scripted test decisions and saves all outputs beside the disposable database.

```powershell
$env:UIPATH_CLI = $uip
& $python -B "$p/Tests/test_seven_division_demo.py" $cfg --render
& $python -B "$p/Tests/verify_seven_division_report.py" `
  'deliverables/Seven-Division-Demo/evidence' `
  'frontend/public/demo/divisions/expected-consolidated.xlsx'
```

For the negative exercises, start a separate fresh automated-test instance. Before its first robot invocation, copy the fixture manifest into its work root, point `division_manifest` in that case’s config to the copy, and pass `--failures` in place of `--render`. On a completed automated-test run, a copied config with new `bundle_id` and `revision` supports `--report-revision reject` without importing more data.

The installed CLI emitted existing warnings about unavailable .NET compiler/signing features, skipped unauthenticated tenant feeds and the missing Automation Hub association. The frontend build emitted its existing chunk-size warning. The live acceptance covers the local Windows setup above.

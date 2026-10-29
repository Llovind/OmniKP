# Mapping benchmark v1

Run from backend:

```powershell
python benchmark_mapping.py --repeats 3
python benchmark_mapping.py --live-ai --repeats 3 --output evidence/mapping-benchmark-live.json
```

The live option sends generated synthetic headers and sample values to the configured provider. It never reads KPI_data. Both commands use a disposable SQLite database; existing application data is preserved.

## Measurements

- Column accuracy: exact target matches / all labelled columns. Wide location names must match exactly.
- Active-column accuracy: same calculation excluding expected ignored columns, to avoid inflating accuracy through irrelevant columns.
- Corrections required: number of proposed column targets differing from the label. This is not an observed human correction count.
- Preview time: parsing, mapping, validation and staging, including provider latency in live mode.
- Reviewed import time: validation and confirmation after automatically supplying the ground truth. Human review time is excluded.
- Import check: each case must import exactly 100 readings after correction. This verifies counts, not every normalized cell value.

Five author-labelled synthetic CSV layouts cover conventional English, Indonesian aliases, unfamiliar semantic headers, reordered unfamiliar headers, and wide Actual/ACH columns. All have synthetic values. The unfamiliar and reordered cases share vocabulary and are not independent samples. No held-out real-world generalization claim is supported. Do not change rules against this suite and present the same suite as independent validation.

LLM columns record whether the provider actually supplied suggestions. A fallback run must remain in reliability results but must not be described as successful AI interpretation. Record model and repeat distribution. Temperature zero does not guarantee repeatability.

## Human comparison still required

Use sanitized, owner-approved division input reports with independently checked mappings and expected consolidated values. Keep completed consolidated workbooks as reference outputs, not interchangeable raw inputs. Include merged headers, local targets, formulas, missing values and changed layouts; count unsupported layouts and failed imports.

Have an analyst perform equivalent tasks manually in Excel and with omniKPI. Counterbalance task order across matched report sets to limit practice effects. Start timing when the source files are opened; stop when the consolidated output has been checked. Include correction, review, retry and validation time. Record final value accuracy as well as speed. Do not use AI processing latency as a substitute for human task duration.

Record each trial in human_trials.csv. Leave unknown values blank. Calculate time savings only for comparable tasks with equivalent accepted output quality: (manual_seconds - assisted_seconds) / manual_seconds. Report participant count, task count, median, range, failures, and mapping corrections. No savings claim is available until these observations exist.

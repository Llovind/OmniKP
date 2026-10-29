# omniKPI synthetic validation pack

This is a reconstructed reporting scenario, not Infranexia operational performance. Unit assignments, KPI names, units and measurement directions follow the June WISA reference structure. All targets, readings, locations and explanations are fictional. The two demo locations are flat reporting locations; this pack does not reproduce the original geographic roll-up hierarchy or its local target exceptions.

## Validate the successful path

1. Open a clean normal workspace at /app. The one-click demo already contains these readings, so uploading them there correctly produces conflicts.
2. Upload the seven unit files: ED, BGES & OLO, NETOP OSP, AIM, FBB, MBB and DEFA. Select the matching submitting unit, Report worksheet, header row 4, one header level, and reporting date 2026-06-30. The in-app Load buttons do this for you.
3. Review mappings. REAL columns hold readings; ACH columns are ignored. Confirm each report after validation.
4. Select 2026-06-30 and All divisions. Expect 90 KPIs, 180 readings, 7 units and 2 fictional locations: Demo North and Demo South. Expect 121 meeting target and 59 missing target.
5. Compare each reading with expected-consolidated.xlsx, Expected readings. Compare actual, target, unit, direction, attainment, status, submitting unit, source filename and row. validation-summary.json provides totals and SHA-256 checksums for the seven inputs. expected-readings.json provides the machine-readable reference.
6. ED / Compliance Deployment Supervision / Demo North has synthetic feedback. Request its explanation. MBB has no attached feedback: expect insufficient evidence until feedback is supplied. AI availability may change drafting; the attributed fallback remains usable without a key.
7. Upload any successful input again: expect duplicate rejection and no added readings.

## Separate failure exercises

Run these before importing ED, or in a separate clean local database. Never count these files as successful divisional inputs. Header row 1; date 2026-06-30; unit ED.

- missing-value.xlsx: first Actual is blank. Validation must reject the entire import; the other valid row must not slip through.
- duplicate-reading.xlsx: repeats a KPI/location/date inside the file. Confirmation must be blocked.
- changed-headers.xlsx: renamed KPI and Actual headers. Map Performance measure to KPI name and Observed outcome to Actual value, then validate. AI can suggest these meanings if enabled, but manual review remains required.

## Reference method

The reference is calculated by validate_demo_pack.py directly from exported worksheet cells using explicit fixture layouts. It does not call omniKPI intake, mapping, target-status or attainment helpers. The reference also reconciles against the generator's intended inputs. This reduces shared-implementation errors; it is not independent third-party certification or proof of real-world AI accuracy.

Achievement is actual/target for higher-is-better and target/actual for lower-is-better, multiplied by 100. Equal zeros give 100. A zero denominator with unequal values gives n.a.; this is never silently converted to zero. Target status is based on direct comparison, even when the attainment ratio is unavailable.

The one-click demo seeds exactly the same seven input files in a separate SQLite database. Reset affects only that shared synthetic demo. A changed fixture version automatically rebuilds it on the next Try demo.

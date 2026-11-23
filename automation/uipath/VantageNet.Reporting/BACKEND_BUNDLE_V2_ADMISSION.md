# Backend report bundle v2 admission

`AdmitBackendReportBundleV2.cs` is an independent coded workflow. The existing synthetic v1 adapter and guards retain their own entry point and staging location. This workflow ends at admission.

## Trusted inputs

Provide the VantageNet.Reporting project folder and these values from the designated disposable run:

| Argument | Expected value |
|---|---|
| `backendOrigin` | Pinned `http://127.0.0.1:<port>` origin with an explicit port. |
| `domainId` | Telecommunications domain `1`. |
| `expectedInstanceId` | A unique ID configured for this run. The backend's default disposable ID is refused. |
| `expectedDatabase` | Exact `sqlite:disposable_<name>.db` or `sqlite:disposable-<name>.db` label from the independently designated DB. |
| `submissionId`, `factId` | Confirmed submission UUID and selected positive fact ID. |
| `bundleId`, `revision` | Report case identifier and explicit `v<number>` revision. |

The workflow retrieves the instance identity and confirmed ledger from the pinned origin before requesting the report bundle. The transport disables redirects, proxies, and cookies. There is no entry point for admitting manually supplied JSON. The local process and its configuration are trusted to be the designated disposable backend. Its identity fields and loopback transport do not provide cryptographic authentication.

The export POST can invoke the provider. Phase 1B exercised it only through a fixture HTTP handler. Run an actual export only during separately authorized acceptance.

## Admission and artifacts

The consumer verifies both schema versions, the source and dataset, producer identity and UTC capture time, the confirmation ledger, the exact fact and its source, feedback and citation relationships, the provider status combination, and the Python-compatible reading digest. The v2 reading digest covers the submission fingerprint, reading, and ordered feedback records. The workflow also computes a separate SHA-256 over the original HTTP response bytes.

Artifacts are published as a unit under `Output/BackendReportBundlesV2/case-<bundleId>/<revision>/`:

- `bundle.json` contains the exact response bytes.
- `state.json` carries the eligibility flag, evidence and provider status, and binding metadata. `live_provider_verified` remains false.
- `snapshot.json` exists only for `draft_ready`. Its `bundle_binding` matches the state binding. The state also records the staged snapshot SHA-256.

Exact-byte replay of the current revision reuses its immutable files. Changed bytes need a new revision. A higher numeric revision for the same case supersedes older revisions, including when the new state is blocked. Earlier files remain available as evidence. The exporter may return different bytes for repeated requests, so continue from the staged state in Phase 1C without making another export request to resume.

Phase 1C must independently verify the current revision under the case lock, recheck archive and snapshot hashes, and bind the actual human decision and output to these artifacts. The estimate of chart support in the bundle should inform template eligibility. Provider/model labels and the `operator-api` origin do not prove live provider use or authenticated feedback authorship. Live acceptance still needs independently observed evidence.

## Offline verification

Run `python -B Tests/test_backend_bundle_v2.py -v` with a .NET 10 SDK available or set `VANTAGENET_DOTNET` to the SDK's `dotnet` executable. The test compiles the production admission modules in a temporary project with no package feeds. Its mock transport serves fixture bytes, and CPython independently computes each digest expectation.

# Faizh integration handoff — after Sprint 4.3

**Admission is currently closed.** Faizh owns backend data, feedback, AI/RCA and consistency/provenance contracts. Lazuardi owns UiPath orchestration, human review, recovery and PPTX generation. This document proposes the smallest integration boundary; it does not introduce an endpoint or change an existing contract.

Read: VantageNet/VANTAGENET.md, VantageNet/ROLE_LAZUARDI.md (actual filename casing), VantageNet/ROLE_FAIZH.md, the schema below, AdaptReportBundle.cs and its actual synthetic fixture. Older planning statements are not evidence of implemented integration.

**Verified:** human-authorized disposable ED import of 26 readings; genuine narrative approval and rendered PPTX for a separate one-reading synthetic snapshot; 10 offline bundle-adapter runtime tests, including old-approval rejection after data changes. **Not verified:** genuine backend report-bundle admission, live AI RCA, genuine operator feedback integration, Action Center or notification delivery. Heatmap/anomalies/RCA availability below is source-inspected, not a claim of successful live endpoint/provider tests.

## 1. Exact current proposed bundle boundary

The consumer is the local-file workflow AdaptReportBundle.cs. Complete existing example: Data/s43-report-bundle.synthetic.json. There is no report-bundle API currently implemented or agreed.

| Field | Required type / validation implemented by the adapter |
|---|---|
| contract; schema_version | string `vantagenet.report-bundle`; integer `1`; unknown versions refused |
| bundle_id | string matching `^[A-Za-z0-9_-]{1,48}$` |
| revision | string matching `^v[1-9][0-9]{0,5}$` |
| source_kind; ai_invoked | `synthetic-fixture`; boolean false only |
| dataset | explicit string `submitted` |
| evidence_status | `draft_ready`, `awaiting_feedback`, `insufficient_evidence`, or `provider_unavailable` |
| scope | nonempty string division, report_date, submission_id; date must parse exactly as yyyy-MM-dd |
| snapshot | object: schema_version integer 1, origin `synthetic-local-fixture`, run_id exactly `<bundle_id>-<revision>`; submission_id/division/report_date equal scope |
| snapshot.reading | nonempty string fact_id, kpi_name, location_name, unit, status, source_file; positive integer source_row; date/division equal scope; finite numeric actual_value >=0 and target_value >0 |
| snapshot.feedback | fact_id string equal to reading.fact_id; origin `synthetic-fixture-not-human-feedback` |
| snapshot.narrative | origin `synthetic-script-not-live-RCA`; when draft_ready, nonempty draft string <=600 characters and nonempty references array |

The example includes feedback.text and narrative.references records `{id:string,text:string}` for display. Those reference-member shapes and citation meaning are **not fully validated** by the adapter; a nonempty array is not proof of valid evidence. Original narrative/approved narrative versions remain separate. Frozen review also limits the reviewed narrative to 600 characters/10 conservatively wrapped lines, reviewer to 60 characters, and single-line rationale to 200.

Only draft_ready produces a staged snapshot. It receives bundle_binding containing contract `vantagenet.report-bundle/1`, revision and the exact input-file SHA-256. Other statuses preserve the bundle/state but produce no reviewable snapshot. Same bytes replay unchanged; changed bytes under the same bundle_id/revision are rejected. Use a new revision/run and obtain a fresh human decision. A hash detects local mutation; it does not authenticate the producer or prove source truth.

**Do not send real data with synthetic labels.** source_kind=backend-read-bundle or ai_invoked=true is explicitly refused. Frozen narrative review likewise accepts only synthetic origins. Real admission requires a mutually agreed extension/version and separately tested UiPath work; it cannot be unlocked by relabeling payloads or setting an approval flag.

## 2. Existing sources versus missing delivery contract

All paths below have prefix `/api/v1/domains/1`. Existing request/response contracts remain unchanged.

| Existing route | Available information | Gap / required join |
|---|---|---|
| GET /submissions/{submission_id} | exact submission status, scope, fingerprint/mapping; readings with fact_id, KPI/location names, date, actual/target/unit, source_file/source_row/submission_id | Provenance anchor verified in prior disposable integration; lacks backend status/direction, feedback text and RCA |
| GET /submissions | confirmed ID, division/date/file, count, confirmed_at | Ledger only; not full report data |
| GET /heatmap?dataset=submitted&division=ED&date=2026-06-30 | fact_id/kpi_id, location ID/name, values/unit/status/direction, provenance, feedback_count and summaries | Join by fact_id to exact submission membership. Date/division may include multiple submissions. feedback_count is not evidence text; omitted date means latest |
| GET /anomalies with the same explicit filters | selected shortfalls, fact/kpi/location IDs, values/status/date/division, anomaly_reason | Not complete provenance or a causal explanation; do not treat target failure as verified RCA |
| GET /kpis/{id}/history?location_id=...&as_of=... | bounded history/status | Not an immutable report snapshot or exact-submission feedback source |
| POST /feedback | creates feedback, returns feedback_id | Write operation, not a retrieval contract. No GET feedback-text route was found in the inspected routers |
| POST /rca | source supports evidence_status, narrative/actions, feedback evidence/references, exact fact/date/division, model/ai_invoked/grounding | Can call provider; not a read-only report export. Live RCA and failure behavior require Faizh verification |

Missing: one versioned consistent bundle, explicit producer/environment identity, capture/revision semantics, retrievable exact-fact feedback content, and verified live narrative/evidence mapping. The draft export/file contract must specify domain_id, disposable instance/environment identity, captured_at, selected fact_id and source response hashes or equivalent revision evidence. **These are requirements to agree for real admission, not fields already enforced by the current synthetic envelope.**

## 3. Minimum backend work and identity invariants

The smallest delivery can be a backend-produced immutable JSON file from a consistent read transaction over existing data, plus a verified RCA result tied to that data. A new HTTP endpoint is not mandatory. If existing APIs are composed instead, Faizh must define a version/recheck protocol that detects changes between reads; separately hashing unrelated GET responses is insufficient to prove consistency. Do not require UiPath to read SQLite directly.

Keep the first report scoped to **one selected reading**; the frozen template is not an aggregate report for all 26 imported readings. Faizh must deliver backend-calculated status and values; UiPath must not reproduce KPI calculations or replace missing/unsupported target values. Zero/negative targets or other values unsupported by the provisional chart must block pending an agreed layout extension.

Identity chain, enforced by producer and checked by the future consumer:

`environment/domain → confirmed submission → fact_id → KPI/location/period → feedback records → cited references → narrative version → bundle revision/hash → new UiPath snapshot/run → human decision → PPTX receipt`

- Select fact_id from the authorized submission's readings; never select the latest reading with the same KPI. Cross-check scope, values, location, file/row and submission across joined responses.
- Normalize integer backend IDs to lossless strings at the agreed boundary; retain kpi_id/location_id for verification. A matching name/date is insufficient identity.
- Every feedback record must retain feedback_id, selected fact_id, explanation, corrective_action, created_at and author/origin when available. Preserve whether it was fixture feedback or genuinely entered by an operator.
- Each reference, such as F123, must resolve to that feedback record for the same fact. Retain cited_feedback_ids and model/ai_invoked/grounding metadata. Structural citation checks do not prove a reported cause is true.
- Narrative text/version and feedback revisions must belong to the same captured data version. Human edits remain human-reviewed text, not automatically AI-verified claims.
- Any change to readings, feedback, references, narrative or included scope requires a new bundle revision/run/snapshot hash and fresh human review. Never copy an old approval into the new run or mutate a frozen snapshot in place.

## 4. Error/status agreement

| Backend situation | Required backend evidence | UiPath behavior after an agreed mapping |
|---|---|---|
| Missing feedback | awaiting_feedback; exact fact identity; no fabricated explanation. Source currently avoids the model when no feedback exists | Preserve blocked bundle/state; no reviewable snapshot/PPTX; request genuine feedback through a separately authorized process |
| Insufficient evidence | insufficient_evidence, evidence references and truthful ai_invoked/model state (a model may already have been called) | Block narrative-ready admission; request better evidence, not an invented cause |
| Missing configuration, provider failure, invalid citations | truthful error/diagnostic; current RCA may return HTTP 503 | Map to proposed provider_unavailable only by agreement; retain failure, do not mark draft_ready or substitute scripted text; no blind write retry |
| Source ai_draft | verified exact-fact draft, evidence, citations and provider trace | Not automatically draft_ready. Faizh validates and demonstrates the mapping before Lazuardi implements live admission |
| Snapshot/revision changes or cross-response mismatch | new revision or explicit consistency failure | Reject stale content/old approval; stage a distinct run only after consistency is established |

`draft_ready` and `provider_unavailable` are **local normalization names**, not claimed backend response strings. Current synthetic blocked-status tests used ai_invoked=false; they do not demonstrate handling real model-invoked responses. No fallback live RCA is permitted. Notifications remain disabled regardless of status.

## 5. One synthetic example matching the actual proposed schema

This is test input, not a live RCA result or operator feedback. draft_ready means a scripted test draft is available for future review, not that sufficient real evidence or human approval exists.

```json
{
  "contract": "vantagenet.report-bundle",
  "schema_version": 1,
  "bundle_id": "s43-bundle-fixture",
  "revision": "v1",
  "source_kind": "synthetic-fixture",
  "ai_invoked": false,
  "dataset": "submitted",
  "evidence_status": "draft_ready",
  "scope": {
    "division": "ED",
    "report_date": "2026-06-30",
    "submission_id": "synthetic-report-fixture-not-import-evidence"
  },
  "snapshot": {
    "schema_version": 1,
    "origin": "synthetic-local-fixture",
    "run_id": "s43-bundle-fixture-v1",
    "submission_id": "synthetic-report-fixture-not-import-evidence",
    "division": "ED",
    "report_date": "2026-06-30",
    "reading": {
      "fact_id": "synthetic-fact-001",
      "kpi_name": "Synthetic deployment KPI",
      "location_name": "Demo North",
      "date": "2026-06-30",
      "division": "ED",
      "actual_value": 97.8,
      "target_value": 98.5,
      "unit": "%",
      "source_file": "synthetic-report-fixture.json",
      "source_row": 1,
      "status": "Below target — explicitly supplied synthetic fixture label"
    },
    "narrative": {
      "origin": "synthetic-script-not-live-RCA",
      "draft": "Synthetic review text: operator feedback is needed before drawing a causal conclusion.",
      "references": [{
        "id": "F1",
        "text": "Synthetic fixture source, not actual operator feedback."
      }]
    },
    "feedback": {
      "origin": "synthetic-fixture-not-human-feedback",
      "fact_id": "synthetic-fact-001",
      "text": "Synthetic test source: no genuine operator feedback has been collected."
    }
  }
}
```

## 6. Integration checklist — Faizh's admission deliverables

- [ ] Supply designated disposable backend identity/base URL/domain, startup instructions and selected confirmed submission/fact IDs; no production database or demo reseed.
- [ ] Agree the real bundle version/source provenance and field/status mapping with Lazuardi, including honest separation from the current synthetic-only envelope.
- [ ] Deliver a consistent one-reading export and reproducible read/recheck procedure, with bundle revision/capture identity and exact submission provenance.
- [ ] Deliver exact-fact feedback records/reference mapping, with origin/author/time and fixture-versus-human status documented.
- [ ] Demonstrate genuine provider RCA on that same fact and retain redacted trace, model/ai_invoked/grounding/citation results; no credentials in handoff artifacts.
- [ ] Deliver observable no-feedback, insufficient-evidence and provider-failure examples; confirm no invented replacement narrative or cross-fact citations.
- [ ] Jointly agree acceptance outcomes below. Lazuardi then implements/tests a separate live-admission extension; do not alter frozen guards merely to force admission.

**Faizh need not implement PPTX, approvals, notification transport or a new export endpoint solely for this handoff.** The blocking backend deliverable is trustworthy, consistent, scoped data/evidence with a verified serialization/error contract. Lazuardi's separate admission extension is also required before real bundles can enter the frozen review/PPTX path.

## 7. Minimum joint real-backend acceptance test — future, not executed here

On the designated disposable backend, retain the existing 26-reading ED import and select one exact fact from it. Faizh and Lazuardi compare submission detail plus explicitly filtered status data, then resolve feedback and references for that fact. Any necessary feedback creation/provider invocation must be separately authorized for that future session; this document authorizes no writes.

Faizh supplies a consistent, versioned one-reading bundle and actual verified provider draft with truthful provenance. After the agreed live extension exists, Lazuardi consumes it without relabeling it synthetic, prepares a **new** run and obtains a genuine fresh narrative decision. Generate one local PPTX, compare all values/provenance/references/approved text with the bundle, open/render it and replay without another finalized report. Ledger/readings must remain unchanged; notifications stay disabled.

In the same acceptance set, change one value or feedback/narrative version in a separate test revision: the old approval must fail and no report may be generated. Demonstrate all three blocked evidence/provider cases without a false draft or distribution. Preserve requests/responses, bundle/version/hash, actual human decision, receipt, rendered proof and unchanged ledger evidence. Passing mocked/synthetic tests alone does not satisfy this real-backend acceptance test.

Documentation-only handoff: no backend/API implementation, frozen workflow, existing contract, approval or test evidence was changed. No live writes, notifications, commit, push, publish or deployment.

# VantageNet report bundle v2

`POST /api/v1/domains/{domain_id}/report-bundles` and `export_report_bundle.py` produce a one-reading `vantagenet.report-bundle` with `schema_version: 2`, `source_kind: backend-read-bundle`, and `dataset: submitted`. The request must select an exact fact from a confirmed submission in the specified domain.

The exporter captures the submission fingerprint, reading, and exact-fact feedback in one database SELECT. It materializes the results and releases the read connection before calling the provider. The RCA prompt, exported feedback records, and citation references all use that capture. New feedback committed during drafting appears only in a later capture. `producer.captured_at` identifies the time the snapshot was read, before drafting begins.

## Provider metadata

Two additive fields live under `snapshot.narrative`. Both existing `ai_invoked` fields agree and indicate that the SDK completion call was attempted.

| Bundle `evidence_status` | `provider_status` | `provider_error_code` | `ai_invoked` |
|---|---|---|---|
| `awaiting_feedback` | `not_attempted` | null | false |
| `provider_unavailable` | `not_attempted` | `missing_configuration` | false |
| `provider_unavailable` | `attempted_unconfirmed` | `request_failed` or `timeout` | true |
| `provider_unavailable` | `response_rejected` | `invalid_response` or `invalid_citations` | true |
| `insufficient_evidence` | `response_accepted` | null | true |
| `draft_ready` | `response_accepted` | null | true |

`attempted_unconfirmed` means the SDK call failed before returning a completion object. Delivery and provider processing remain unknown, including after a timeout. `response_rejected` means a returned completion failed application validation. `response_accepted` means the completion passed validation, including a valid insufficient-evidence response. The configured `llm_model` identifies the model requested on accepted completions. A live acceptance run still requires independent provider evidence. Failure text is fixed and excludes SDK exception details and raw provider output.

Only `draft_ready` supplies a reviewable draft. Require its accepted completion, verified structural grounding, and declared citations that resolve to exact-fact feedback records with matching origin. Inline `[F<id>]` tokens resolve by numeric ID and must be a nonempty subset of the declared IDs. For `insufficient_evidence`, the references list is the captured evidence and the citation-verified flag is false. The direct `POST /rca` route retains its response shape and its 503 error response for unavailable providers or rejected completions.

## Reading digest and revisions

`producer.reading_sha256` is the lowercase SHA-256 hex digest of the UTF-8 bytes produced by this serialization, with no BOM or trailing newline.

```python
json.dumps(
    {
        "submission_fingerprint": bundle["producer"]["submission_fingerprint"],
        "reading": bundle["snapshot"]["reading"],
        "feedback": bundle["snapshot"]["feedback"]["records"],
    },
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
```

The encoding uses Python JSON string escaping and number formatting. Object keys are sorted at every level, Unicode characters are written directly where JSON allows them, and arrays retain their order. Feedback records are ordered by numeric feedback ID ascending. Their feedback and fact IDs are JSON strings, as are the reading's fact, KPI, and location IDs. A consumer that recomputes this digest needs serialization parity with Python, including numeric and Unicode cases. The digest covers the reading and evidence, plus the submission fingerprint. Capture time, revision, narrative, and envelope metadata fall outside this digest.

The caller supplies `bundle_id` and `revision`; the exporter validates syntax. Repeating an export can call the provider again and return different bytes under the same revision, even when `reading_sha256` matches. Archive the successful response bytes and use a separate full-byte SHA-256 for replay and approval binding. Publish changed content under a new revision and obtain a fresh approval. Backend-enforced idempotency would require a separate design for durable revision ownership and storage.

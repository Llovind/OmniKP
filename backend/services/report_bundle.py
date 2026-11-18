"""Consistent single-reading report bundle exporter for VantageNet."""
import hashlib
import json
import re
from sqlalchemy.orm import Session

from agents.feedback_rca import run_rca
from database import (
    DimKPI,
    DimLocation,
    DimPeriod,
    DivisionFeedback,
    FactKPI,
    ReadingSource,
    Submission,
    get_disposable_instance_info,
)
from services.intake import now
from services.performance import attainment, target_status

BUNDLE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,48}$")
REVISION_RE = re.compile(r"^v[1-9][0-9]{0,5}$")


def _status_label(status_code: str, higher_is_better: bool) -> str:
    if status_code == "RED":
        return "Below target" if higher_is_better else "Above allowed limit"
    if status_code == "GREEN":
        return "Meeting target"
    return "Target unavailable"


async def build_report_bundle(
    db: Session,
    domain_id: int,
    submission_id: str,
    fact_id: int,
    bundle_id: str = "backend-bundle",
    revision: str = "v1",
) -> dict:
    """Build a versioned, provenance-linked one-reading bundle in a single read session."""
    if not BUNDLE_ID_RE.fullmatch(bundle_id):
        raise ValueError("Invalid bundle_id: use 1–48 characters from [A-Za-z0-9_-].")
    if not REVISION_RE.fullmatch(revision):
        raise ValueError("Invalid revision: use v<integer> (for example v1).")

    submission = (
        db.query(Submission)
        .filter_by(domain_id=domain_id, submission_id=submission_id)
        .first()
    )
    if not submission:
        raise LookupError("Submission not found in this domain.")
    if submission.status != "confirmed":
        raise ValueError("Report bundle requires a confirmed submission.")

    row = (
        db.query(ReadingSource, FactKPI, DimKPI, DimLocation, DimPeriod)
        .join(FactKPI, ReadingSource.fact_id == FactKPI.fact_id)
        .join(DimKPI, FactKPI.kpi_id == DimKPI.kpi_id)
        .join(DimLocation, FactKPI.location_id == DimLocation.location_id)
        .join(DimPeriod, FactKPI.period_id == DimPeriod.period_id)
        .filter(
            ReadingSource.submission_id == submission.submission_id,
            ReadingSource.fact_id == fact_id,
            FactKPI.domain_id == domain_id,
        )
        .first()
    )
    if not row:
        raise LookupError("Confirmed reading not found for this submission and fact_id.")

    source, fact, kpi, loc, period = row
    feedback_entries = (
        db.query(DivisionFeedback)
        .filter_by(fact_id=fact.fact_id)
        .order_by(DivisionFeedback.feedback_id.asc())
        .all()
    )

    status_code = target_status(fact.actual_value, fact.target_value, kpi.higher_is_better)
    reading_record = {
        "fact_id": str(fact.fact_id),
        "kpi_id": str(kpi.kpi_id),
        "location_id": str(loc.location_id),
        "kpi_name": kpi.kpi_name,
        "kpi_archetype": kpi.kpi_archetype,
        "location_name": loc.location_name,
        "date": period.date,
        "division": source.division,
        "actual_value": fact.actual_value,
        "target_value": fact.target_value,
        "unit": kpi.unit or "",
        "higher_is_better": bool(kpi.higher_is_better),
        "attainment_pct": attainment(fact.actual_value, fact.target_value, kpi.higher_is_better),
        "source_file": submission.filename,
        "source_row": source.source_row,
        "status_code": status_code,
        "status": _status_label(status_code, bool(kpi.higher_is_better)),
        "chart_supported": bool(
            fact.target_value is not None and fact.target_value > 0 and fact.actual_value >= 0
        ),
    }

    feedback_records = [
        {
            "feedback_id": str(f.feedback_id),
            "reference": f"F{f.feedback_id}",
            "fact_id": str(f.fact_id),
            "division": f.division,
            "explanation": f.explanation,
            "corrective_action": f.corrective_action,
            "origin": getattr(f, "origin", "operator-api") or "operator-api",
            "created_at": f.created_at,
        }
        for f in feedback_entries
    ]
    origins = {r["origin"] for r in feedback_records}
    if not origins:
        feedback_origin = "none"
    elif len(origins) == 1:
        feedback_origin = next(iter(origins))
    else:
        feedback_origin = "mixed"

    by_id = {r["feedback_id"]: r for r in feedback_records}
    rca = None
    provider_error = None
    try:
        rca = await run_rca(db, domain_id, kpi.kpi_id, loc.location_id, fact.fact_id)
    except RuntimeError as exc:
        provider_error = str(exc)

    if provider_error is not None or rca is None:
        evidence_status = "provider_unavailable"
        narrative_origin = "provider-error"
    elif rca["evidence_status"] == "ai_draft":
        evidence_status = "draft_ready"
        narrative_origin = "live-provider-rca"
    elif rca["evidence_status"] == "awaiting_feedback":
        evidence_status = "awaiting_feedback"
        narrative_origin = "backend-deterministic-gate"
    elif rca["evidence_status"] == "insufficient_evidence":
        evidence_status = "insufficient_evidence"
        narrative_origin = "live-provider-rca"
    else:
        raise RuntimeError(f"Unsupported RCA status for bundle export: {rca['evidence_status']}")

    if evidence_status == "draft_ready" and rca:
        cited_ids = [str(fid) for fid in rca.get("cited_feedback_ids", [])]
    elif evidence_status == "insufficient_evidence":
        cited_ids = [r["feedback_id"] for r in feedback_records]
    else:
        cited_ids = []

    references = []
    for fid in cited_ids:
        rec = by_id.get(fid)
        if not rec:
            continue
        text = rec["explanation"]
        if rec["corrective_action"]:
            text = f"{text} Proposed action: {rec['corrective_action']}"
        references.append({
            "id": rec["reference"],
            "feedback_id": rec["feedback_id"],
            "origin": rec["origin"],
            "text": text,
        })

    canonical_source = json.dumps(
        {
            "submission_fingerprint": submission.fingerprint,
            "reading": reading_record,
            "feedback": feedback_records,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    reading_sha256 = hashlib.sha256(canonical_source).hexdigest()

    instance = get_disposable_instance_info()
    return {
        "contract": "vantagenet.report-bundle",
        "schema_version": 2,
        "bundle_id": bundle_id,
        "revision": revision,
        "source_kind": "backend-read-bundle",
        "ai_invoked": bool(rca["ai_invoked"]) if rca else False,
        "dataset": "submitted",
        "evidence_status": evidence_status,
        "producer": {
            "domain_id": domain_id,
            "disposable": instance["disposable"],
            "instance_id": instance["instance_id"],
            "captured_at": now(),
            "submission_fingerprint": submission.fingerprint,
            "reading_sha256": reading_sha256,
        },
        "scope": {
            "division": source.division,
            "report_date": period.date,
            "submission_id": submission.submission_id,
            "fact_id": str(fact.fact_id),
        },
        "snapshot": {
            "schema_version": 2,
            "origin": "backend-confirmed-submission",
            "run_id": f"{bundle_id}-{revision}",
            "submission_id": submission.submission_id,
            "division": source.division,
            "report_date": period.date,
            "reading": reading_record,
            "feedback": {
                "fact_id": str(fact.fact_id),
                "count": len(feedback_records),
                "origin": feedback_origin,
                "records": feedback_records,
                "text": (
                    " | ".join(f"[{r['reference']}] {r['explanation']}" for r in feedback_records)
                    if feedback_records
                    else "No division feedback recorded for this reading."
                ),
            },
            "narrative": {
                "origin": narrative_origin,
                "backend_evidence_status": rca["evidence_status"] if rca else "provider_error",
                "llm_model": rca["llm_model"] if rca else "not available",
                "ai_invoked": bool(rca["ai_invoked"]) if rca else False,
                "grounding": (
                    {
                        "cited_feedback_ids": [str(fid) for fid in rca["grounding"].get("cited_feedback_ids", [])],
                        "structural_check": bool(rca["grounding"].get("structural_check")),
                        "citation_verified": bool(rca["grounding"].get("citation_verified")),
                    }
                    if rca
                    else {
                        "cited_feedback_ids": [],
                        "structural_check": False,
                        "citation_verified": False,
                    }
                ),
                "cited_feedback_ids": [str(fid) for fid in rca.get("cited_feedback_ids", [])] if rca else [],
                "root_cause": rca["root_cause"] if rca and evidence_status != "provider_unavailable" else None,
                "prescriptive_action": (
                    rca["prescriptive_action"] if rca and evidence_status != "provider_unavailable" else None
                ),
                "draft": (
                    f"{rca['root_cause']} Recommended action: {rca['prescriptive_action']}"
                    if rca and evidence_status == "draft_ready"
                    else None
                ),
                "references": references,
                "error": provider_error,
            },
        },
    }

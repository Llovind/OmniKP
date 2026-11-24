"""Read-only snapshot and evidence-linked draft for the seven-division demo."""

from collections import defaultdict

from agents.feedback_rca import RCAProviderError, draft_from_evidence, feedback_evidence
from database import DimPeriod, DivisionFeedback, FactKPI, get_disposable_instance_info
from routers.kpi import report_query
from services.intake import now
from services.performance import attainment, relative_target_gap, target_status
from services.report_bundle import BUNDLE_ID_RE, REVISION_RE


def summarize(readings):
    return {
        "kpis": len({r["kpi_id"] for r in readings}),
        "readings": len(readings),
        "locations": len({r["location_id"] for r in readings}),
        "meeting": sum(r["status"] == "GREEN" for r in readings),
        "below_target": sum(r["status"] == "RED" for r in readings),
        "target_unavailable": sum(r["status"] == "YELLOW" for r in readings),
    }


def capture(db, domain_id, day, submission_ids):
    # One SELECT reads the period, exact sources and all matching feedback.
    rows = (report_query(db, domain_id).outerjoin(DivisionFeedback, DivisionFeedback.fact_id == FactKPI.fact_id)
            .add_entity(DivisionFeedback).filter(DimPeriod.date == day)
            .order_by(FactKPI.fact_id, DivisionFeedback.feedback_id).all())
    readings, submissions = {}, {}
    feedback, divisions, locations = defaultdict(list), defaultdict(list), defaultdict(list)
    for fact, kpi, location, period, source, submission, entry in rows:
        if (not source or not submission or submission.status != "confirmed"
                or submission.submission_id not in submission_ids or submission.report_date != day
                or submission.domain_id != domain_id or submission.division != source.division
                or source.source_row < 1):
            raise ValueError("Period contains readings outside the requested confirmed submissions.")
        if entry:
            feedback[fact.fact_id].append(feedback_evidence(entry))
        if fact.fact_id in readings:
            continue
        reading = dict(
            fact_id=fact.fact_id, submission_id=submission.submission_id, division=source.division,
            source_file=submission.filename, source_row=source.source_row, date=period.date,
            kpi_id=kpi.kpi_id, kpi_name=kpi.kpi_name, kpi_archetype=kpi.kpi_archetype,
            location_id=location.location_id, location_name=location.location_name,
            actual_value=fact.actual_value, target_value=fact.target_value, unit=kpi.unit or "",
            higher_is_better=bool(kpi.higher_is_better),
            status=target_status(fact.actual_value, fact.target_value, kpi.higher_is_better),
            attainment_pct=attainment(fact.actual_value, fact.target_value, kpi.higher_is_better),
        )
        readings[fact.fact_id] = reading
        divisions[source.division].append(reading)
        locations[location.location_name].append(reading)
        submissions[submission.submission_id] = dict(
            submission_id=submission.submission_id, division=submission.division, filename=submission.filename,
            fingerprint=submission.fingerprint, report_date=submission.report_date, sheet_name=submission.sheet_name,
            confirmed_at=submission.confirmed_at, row_count=submission.row_count,
        )
    counts = defaultdict(int)
    for reading in readings.values():
        counts[reading["submission_id"]] += 1
    if (set(submissions) != submission_ids or len(divisions) != 7
            or any(counts[sid] != row["row_count"] for sid, row in submissions.items())):
        raise ValueError("Seven complete confirmed division submissions are required for this period.")
    gaps = [r for r in readings.values() if r["status"] == "RED"]
    gaps.sort(key=lambda r: relative_target_gap(r["actual_value"], r["target_value"]), reverse=True)
    return dict(
        readings=list(readings.values()), totals=summarize(readings.values()),
        divisions=[dict(division=name, **summarize(group)) for name, group in sorted(divisions.items())],
        locations=[dict(location=name, **summarize(group)) for name, group in sorted(locations.items())],
        submissions=sorted(submissions.values(), key=lambda r: r["division"]),
        gaps=[dict(fact_id=r["fact_id"], reason="Below target" if r["higher_is_better"] else "Above allowed limit")
              for r in gaps],
        feedback=[entry for group in feedback.values() for entry in group],
    ), gaps, feedback


async def build_aggregate_report(db, domain_id, day, submission_ids, bundle_id, revision):
    identity = get_disposable_instance_info()
    if not identity["disposable"]:
        raise ValueError("Aggregate demo requires an identified disposable backend.")
    if len(submission_ids) != 7 or not BUNDLE_ID_RE.fullmatch(bundle_id) or not REVISION_RE.fullmatch(revision):
        raise ValueError("Provide seven unique submissions and a valid bundle ID and revision.")
    try:
        snapshot, gaps, feedback = capture(db, domain_id, day, submission_ids)
        captured_at = now()
    finally:
        db.rollback()

    # One exact-fact draft keeps the demo predictable. All gap readings remain in the snapshot.
    focus = next((reading for reading in gaps if reading["fact_id"] in feedback), None)
    narrative = dict(evidence_status="insufficient_evidence", ai_invoked=False, fact_id=None)
    if focus:
        try:
            narrative = await draft_from_evidence(focus, feedback[focus["fact_id"]], allow_synthetic_scenario=True)
        except RCAProviderError as exc:
            narrative = dict(evidence_status="provider_unavailable", provider_status=exc.provider_status,
                             provider_error=exc.error_code, ai_invoked=exc.provider_status != "not_attempted",
                             fact_id=focus["fact_id"])

    return dict(contract="vantagenet.aggregate-report", version=1, synthetic=True, dataset="submitted",
                bundle_id=bundle_id, revision=revision, identity=identity, domain_id=domain_id,
                report_date=day, captured_at=captured_at, narrative=narrative,
                shortfalls_with_feedback=sum(r["fact_id"] in feedback for r in gaps), **snapshot)

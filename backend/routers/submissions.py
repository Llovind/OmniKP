"""Competition demo: divisional upload → review → confirm → consolidated readings."""
import json
from datetime import date
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import (
    get_db,
    DimKPI,
    DimLocation,
    DimPeriod,
    DivisionFeedback,
    FactKPI,
    ReadingSource,
    Submission,
)
from dependencies import get_validated_domain
from services.intake import stage, review, confirm, now
from services.performance import attainment, target_status
from services.report_bundle import build_report_bundle

router = APIRouter(prefix='/api/v1/domains/{domain_id}', tags=['Division submissions'],
                   dependencies=[Depends(get_validated_domain)])


class ReviewRequest(BaseModel):
    mapping: dict[str, str]
    default_direction: str | None = None


class FeedbackRequest(BaseModel):
    fact_id: int
    explanation: str = Field(min_length=5, max_length=4000)
    corrective_action: str = Field(default='', max_length=4000)


class ReportBundleRequest(BaseModel):
    submission_id: str
    fact_id: int
    bundle_id: str = 'backend-bundle'
    revision: str = 'v1'


@router.post('/submissions/preview')
async def preview_report(domain_id: int, file: UploadFile = File(...), division: str = Form(...),
                         report_date: date = Form(...), sheet_name: str = Form(''), header_row: int = Form(0),
                         header_depth: int = Form(1), use_ai: bool = Form(False), db: Session = Depends(get_db)):
    content = await file.read(10 * 1024 * 1024 + 1)
    try:
        return await stage(db, domain_id, content, file.filename or '', division, report_date.isoformat(),
                           sheet_name, header_row, header_depth, use_ai)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(503, str(exc))
    except (ValueError, UnicodeError) as exc:
        db.rollback()
        raise HTTPException(422, str(exc))
    except Exception:
        db.rollback()
        raise HTTPException(422, 'Unable to read this report. Check that it is a valid .xlsx or UTF-8 .csv file.')


def get_submission(db, domain_id, submission_id):
    submission = db.query(Submission).filter_by(domain_id=domain_id, submission_id=submission_id).first()
    if not submission:
        raise HTTPException(404, 'Submission not found.')
    return submission


@router.post('/submissions/{submission_id}/review')
def review_report(domain_id: int, submission_id: str, request: ReviewRequest, db: Session = Depends(get_db)):
    try:
        return review(db, get_submission(db, domain_id, submission_id), request.mapping, request.default_direction)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@router.post('/submissions/{submission_id}/confirm')
def confirm_report(domain_id: int, submission_id: str, request: ReviewRequest, db: Session = Depends(get_db)):
    try:
        return confirm(db, get_submission(db, domain_id, submission_id), request.mapping, request.default_direction)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))
    except Exception:
        db.rollback()
        raise


@router.get('/submissions')
def list_submissions(domain_id: int, db: Session = Depends(get_db)):
    return [{"submission_id": s.submission_id, "division": s.division, "filename": s.filename,
             "report_date": s.report_date, "readings": s.row_count, "confirmed_at": s.confirmed_at}
            for s in db.query(Submission).filter_by(domain_id=domain_id, status='confirmed')
            .order_by(Submission.confirmed_at.desc()).all()]


@router.get('/submissions/{submission_id}')
def get_submission_detail(domain_id: int, submission_id: str, db: Session = Depends(get_db)):
    """Return full submission status, approved mapping, fingerprint, and confirmed readings with provenance."""
    submission = get_submission(db, domain_id, submission_id)
    readings = []
    if submission.status == 'confirmed':
        rows = (
            db.query(ReadingSource, FactKPI, DimKPI, DimLocation, DimPeriod)
            .join(FactKPI, ReadingSource.fact_id == FactKPI.fact_id)
            .join(DimKPI, FactKPI.kpi_id == DimKPI.kpi_id)
            .join(DimLocation, FactKPI.location_id == DimLocation.location_id)
            .join(DimPeriod, FactKPI.period_id == DimPeriod.period_id)
            .filter(
                ReadingSource.submission_id == submission.submission_id,
                FactKPI.domain_id == domain_id,
            )
            .order_by(ReadingSource.source_row.asc(), FactKPI.fact_id.asc())
            .all()
        )
        for source, fact, kpi, loc, period in rows:
            readings.append({
                "fact_id": fact.fact_id,
                "submission_id": submission.submission_id,
                "division": source.division,
                "source_file": submission.filename,
                "source_row": source.source_row,
                "date": period.date,
                "kpi_id": kpi.kpi_id,
                "kpi_name": kpi.kpi_name,
                "kpi_archetype": kpi.kpi_archetype,
                "location_id": loc.location_id,
                "location_name": loc.location_name,
                "actual_value": fact.actual_value,
                "target_value": fact.target_value,
                "unit": kpi.unit or "",
                "higher_is_better": bool(kpi.higher_is_better),
                "status": target_status(fact.actual_value, fact.target_value, kpi.higher_is_better),
                "attainment_pct": attainment(fact.actual_value, fact.target_value, kpi.higher_is_better),
            })
    return {
        "submission_id": submission.submission_id,
        "domain_id": submission.domain_id,
        "status": submission.status,
        "division": submission.division,
        "filename": submission.filename,
        "report_date": submission.report_date,
        "sheet_name": submission.sheet_name,
        "fingerprint": submission.fingerprint,
        "mapping": json.loads(submission.mapping_json),
        "row_count": submission.row_count,
        "created_at": submission.created_at,
        "confirmed_at": submission.confirmed_at,
        "readings": readings,
    }


@router.get('/feedback')
def list_feedback(domain_id: int, fact_id: int, db: Session = Depends(get_db)):
    """Retrieve exact-fact division feedback entries with origin provenance."""
    fact = db.query(FactKPI).filter_by(fact_id=fact_id, domain_id=domain_id).first()
    if not fact:
        raise HTTPException(404, 'Reading not found in this domain.')
    source = db.query(ReadingSource).filter_by(fact_id=fact_id).first()
    submission = (
        db.query(Submission).filter_by(submission_id=source.submission_id, domain_id=domain_id).first()
        if source else None
    )
    entries = (
        db.query(DivisionFeedback)
        .filter_by(fact_id=fact_id)
        .order_by(DivisionFeedback.feedback_id.asc())
        .all()
    )
    return {
        "domain_id": domain_id,
        "fact_id": fact_id,
        "submission_id": source.submission_id if source else None,
        "division": source.division if source else None,
        "source_file": submission.filename if submission else None,
        "source_row": source.source_row if source else None,
        "feedback_count": len(entries),
        "feedback": [
            {
                "feedback_id": f.feedback_id,
                "reference": f"F{f.feedback_id}",
                "fact_id": f.fact_id,
                "division": f.division,
                "explanation": f.explanation,
                "corrective_action": f.corrective_action,
                "origin": getattr(f, "origin", "operator-api") or "operator-api",
                "created_at": f.created_at,
            }
            for f in entries
        ],
    }


@router.post('/feedback')
def add_feedback(domain_id: int, request: FeedbackRequest, db: Session = Depends(get_db)):
    fact = db.query(FactKPI).filter_by(fact_id=request.fact_id, domain_id=domain_id).first()
    source = db.query(ReadingSource).filter_by(fact_id=request.fact_id).first()
    if not fact or not source:
        raise HTTPException(404, 'Choose a reading from a confirmed division submission.')
    explanation = request.explanation.strip()
    if len(explanation) < 5:
        raise HTTPException(422, 'Provide a meaningful division explanation.')
    feedback = DivisionFeedback(fact_id=fact.fact_id, division=source.division, explanation=explanation,
                                corrective_action=request.corrective_action.strip(),
                                origin='operator-api', created_at=now())
    db.add(feedback)
    db.commit()
    return {
        "feedback_id": feedback.feedback_id,
        "reference": f"F{feedback.feedback_id}",
        "fact_id": fact.fact_id,
        "division": feedback.division,
        "origin": feedback.origin,
        "created_at": feedback.created_at,
    }


@router.post('/report-bundles')
async def export_report_bundle(domain_id: int, request: ReportBundleRequest, db: Session = Depends(get_db)):
    """Export a consistent, versioned single-reading bundle for report review and PPTX workflows."""
    try:
        return await build_report_bundle(
            db=db,
            domain_id=domain_id,
            submission_id=request.submission_id,
            fact_id=request.fact_id,
            bundle_id=request.bundle_id,
            revision=request.revision,
        )
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))

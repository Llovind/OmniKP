"""Competition demo: divisional upload → review → confirm → consolidated readings."""
from datetime import date
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db, Submission, ReadingSource, DivisionFeedback, FactKPI
from dependencies import get_validated_domain
from services.intake import stage, review, confirm, now

router = APIRouter(prefix='/api/v1/domains/{domain_id}', tags=['Division submissions'],
                   dependencies=[Depends(get_validated_domain)])


class ReviewRequest(BaseModel):
    mapping: dict[str, str]
    default_direction: str | None = None


class FeedbackRequest(BaseModel):
    fact_id: int
    explanation: str = Field(min_length=5, max_length=4000)
    corrective_action: str = Field(default='', max_length=4000)


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
                                corrective_action=request.corrective_action.strip(), created_at=now())
    db.add(feedback)
    db.commit()
    return {"feedback_id": feedback.feedback_id, "division": feedback.division}

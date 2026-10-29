"""
routers/rca.py — RCA Agent trigger endpoint.

POST /api/v1/domains/{domain_id}/rca
    Triggers the RCA Agent for a specified KPI anomaly at a given location.
    Returns: advisory draft, division feedback references, and evidence status.

Advisory mode: AI output requires network engineer review. The system never
executes network configuration changes or remediation commands.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.feedback_rca import run_rca
from database import get_db
from dependencies import get_validated_domain
from schemas import RCARequest, RCAResponse

router = APIRouter(
    prefix="/api/v1/domains/{domain_id}",
    tags=["RCA Agent"],
    dependencies=[Depends(get_validated_domain)],
)


@router.post("/rca", response_model=RCAResponse)
async def trigger_rca(
    domain_id: int,
    request: RCARequest,
    db: Session = Depends(get_db),
):
    """
    Trigger the RCA Agent for a given anomalous KPI at a specific location.

    Request body: { "kpi_id": int, "location_id": int, "fact_id": int }

    The agent reads feedback for the selected fact (exact KPI/location/period).
    No feedback means an insufficient-evidence result without an LLM call.
    Otherwise an advisory draft cites recognized feedback IDs, with an attributed
    excerpt fallback when the provider fails or returns invalid citations.

    If the LLM is unavailable (rate limit, network error), a fallback
    attributed division feedback is returned automatically.
    This keeps the ITASE finalist demo usable when the LLM provider is unavailable.
    """
    try:
        result = await run_rca(
            db=db,
            domain_id=domain_id,
            kpi_id=request.kpi_id,
            location_id=request.location_id,
            fact_id=request.fact_id,
        )
        return RCAResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RCA Agent error: {exc}")

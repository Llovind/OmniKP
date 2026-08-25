"""
routers/rca.py — RCA Agent trigger endpoint.

POST /api/v1/domains/{domain_id}/rca
    Triggers the RCA Agent for a specified KPI anomaly at a given location.
    Returns: root cause, confidence score (from Z-score), prescriptive action.

Advisory mode: AI output is for human review only. The system is read-only with
respect to OT (Purdue Model / ISA-95) — it never issues physical control commands.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agents.rca_agent import run_rca
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

    Request body: { "kpi_id": int, "location_id": int }

    The agent:
      1. Retrieves the latest anomaly fact from fact_kpi
      2. Queries shift_logs_fts (SQLite FTS5) for corroborating log entries
      3. Computes confidence score deterministically from Z-score (not from LLM)
      4. Calls LLM (via OpenRouter) to narrate root cause and prescriptive action
      5. Returns structured JSON — LLM output is advisory, not executable

    If the LLM is unavailable (rate limit, network error), a fallback
    deterministic analysis from shift logs is returned automatically.
    This ensures demo resilience for CALIBER Final Stage (24hr live hackathon).
    """
    try:
        result = await run_rca(
            db=db,
            domain_id=domain_id,
            kpi_id=request.kpi_id,
            location_id=request.location_id,
        )
        return RCAResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RCA Agent error: {exc}")

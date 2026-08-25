"""
dependencies.py — Shared FastAPI dependency functions for OmniKPI / PlantIntel.

Domain isolation rule (from ANTIGRAVITY_PROJECT_CONTEXT.md):
    All routes enforce domain_id via Depends() at router level — never filter manually per-endpoint.
    Valid domain_ids: 1 = telco (ITASE), 2 = petrochemical (CALIBER).
"""
from fastapi import Path, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, DimDomain


async def get_validated_domain(
    domain_id: int = Path(..., description="Domain ID: 1=telco (ITASE), 2=petrochemical (CALIBER)"),
    db: Session = Depends(get_db),
) -> DimDomain:
    """
    Router-level dependency: validates domain_id from the URL path.
    Raises 404 if domain does not exist in dim_domain.
    Attach to any router with: dependencies=[Depends(get_validated_domain)]
    """
    domain = db.query(DimDomain).filter(DimDomain.domain_id == domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=404,
            detail=f"Domain ID {domain_id} not found. Valid options: 1=telco, 2=petrochemical.",
        )
    return domain

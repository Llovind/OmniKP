"""
routers/kpi.py — KPI, location hierarchy, heatmap, and history endpoints.

All routes require domain_id validated at router level via get_validated_domain.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, DimDomain, DimKPI, DimLocation, DimPeriod, FactKPI
from dependencies import get_validated_domain
from schemas import (
    KPIInfo, LocationNode,
    HeatmapResponse, HeatmapLocation, HeatmapCell, LocationSummary,
    HistoryResponse, HistoryPoint,
)

router = APIRouter(
    prefix="/api/v1/domains/{domain_id}",
    tags=["KPI & Heatmap"],
    dependencies=[Depends(get_validated_domain)],
)


# ─── Locations ────────────────────────────────────────────────────────────────

@router.get("/locations", response_model=list[LocationNode])
def list_locations(domain_id: int, db: Session = Depends(get_db)):
    """
    Return the full location hierarchy as a tree.
    Root nodes: parent_location_id = None.
    Uses adjacency list pattern — same schema supports both telco and petrochemical.
    """
    all_locs = (
        db.query(DimLocation)
        .filter(DimLocation.domain_id == domain_id)
        .all()
    )

    # Build map of id → LocationNode
    node_map: dict[int, LocationNode] = {
        loc.location_id: LocationNode(
            location_id=loc.location_id,
            location_name=loc.location_name,
            location_type=loc.location_type,
            parent_location_id=loc.parent_location_id,
            domain_id=loc.domain_id,
        )
        for loc in all_locs
    }

    # Wire children and collect roots
    roots: list[LocationNode] = []
    for loc_id, node in node_map.items():
        if node.parent_location_id is None:
            roots.append(node)
        else:
            parent = node_map.get(node.parent_location_id)
            if parent:
                parent.children.append(node)

    return roots


# ─── KPIs ─────────────────────────────────────────────────────────────────────

@router.get("/kpis", response_model=list[KPIInfo])
def list_kpis(domain_id: int, db: Session = Depends(get_db)):
    """List all KPIs for a domain, ordered by archetype."""
    return (
        db.query(DimKPI)
        .filter(DimKPI.domain_id == domain_id)
        .order_by(DimKPI.kpi_archetype, DimKPI.kpi_name)
        .all()
    )


# ─── Heatmap ──────────────────────────────────────────────────────────────────

@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(domain_id: int, db: Session = Depends(get_db)):
    """
    Return the KPI heatmap for all leaf locations as of the latest period.

    Leaf locations: nodes with no children in the adjacency list.
    Data shape: one row per location, columns per KPI archetype.
    Status: GREEN | YELLOW | RED (pre-computed at seed time from Z-score thresholds).

    This endpoint is the primary data source for the React heatmap matrix component.
    """
    domain = db.query(DimDomain).filter(DimDomain.domain_id == domain_id).first()

    # Latest date in the system
    latest_date: str | None = db.query(func.max(DimPeriod.date)).scalar()
    if not latest_date:
        raise HTTPException(status_code=404, detail="No period data found. Run seed_data.py first.")

    # Identify leaf locations (those NOT referenced as parent_location_id)
    all_locs = db.query(DimLocation).filter(DimLocation.domain_id == domain_id).all()
    parent_ids = {loc.parent_location_id for loc in all_locs if loc.parent_location_id is not None}
    leaf_locs = [loc for loc in all_locs if loc.location_id not in parent_ids]

    result_locations: list[HeatmapLocation] = []

    for loc in leaf_locs:
        rows = (
            db.query(FactKPI, DimKPI)
            .join(DimKPI, FactKPI.kpi_id == DimKPI.kpi_id)
            .join(DimPeriod, FactKPI.period_id == DimPeriod.period_id)
            .filter(
                FactKPI.domain_id == domain_id,
                FactKPI.location_id == loc.location_id,
                DimPeriod.date == latest_date,
            )
            .order_by(DimKPI.kpi_archetype, DimKPI.kpi_name)
            .all()
        )

        cells: list[HeatmapCell] = []
        status_counts: dict[str, int] = {"RED": 0, "YELLOW": 0, "GREEN": 0}

        for fact, kpi in rows:
            st = fact.status or "GREEN"
            cells.append(HeatmapCell(
                kpi_id=kpi.kpi_id,
                kpi_name=kpi.kpi_name,
                kpi_archetype=kpi.kpi_archetype,
                actual_value=fact.actual_value,
                target_value=fact.target_value,
                z_score=fact.z_score,
                is_anomaly=fact.is_anomaly,
                status=st,
                unit=kpi.unit or "",
                higher_is_better=bool(kpi.higher_is_better),
            ))
            status_counts[st] = status_counts.get(st, 0) + 1

        result_locations.append(HeatmapLocation(
            location_id=loc.location_id,
            location_name=loc.location_name,
            location_type=loc.location_type,
            parent_location_id=loc.parent_location_id,
            kpis=cells,
            summary=LocationSummary(
                total=len(cells),
                red=status_counts.get("RED", 0),
                yellow=status_counts.get("YELLOW", 0),
                green=status_counts.get("GREEN", 0),
            ),
        ))

    return HeatmapResponse(
        domain_id=domain_id,
        domain_name=domain.domain_name,
        date=latest_date,
        locations=result_locations,
    )


# ─── KPI History ──────────────────────────────────────────────────────────────

@router.get("/kpis/{kpi_id}/history", response_model=HistoryResponse)
def get_kpi_history(
    domain_id: int,
    kpi_id: int,
    location_id: int = Query(..., description="Leaf location ID"),
    db: Session = Depends(get_db),
):
    """
    30-day historical series for a specific KPI at a specific location.
    Used for the sparkline / detail chart when a heatmap cell is clicked.
    """
    kpi = (
        db.query(DimKPI)
        .filter(DimKPI.kpi_id == kpi_id, DimKPI.domain_id == domain_id)
        .first()
    )
    if not kpi:
        raise HTTPException(status_code=404, detail=f"KPI {kpi_id} not found in domain {domain_id}")

    loc = (
        db.query(DimLocation)
        .filter(DimLocation.location_id == location_id, DimLocation.domain_id == domain_id)
        .first()
    )
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found in domain {domain_id}")

    rows = (
        db.query(FactKPI, DimPeriod)
        .join(DimPeriod, FactKPI.period_id == DimPeriod.period_id)
        .filter(
            FactKPI.kpi_id == kpi_id,
            FactKPI.location_id == location_id,
            FactKPI.domain_id == domain_id,
        )
        .order_by(DimPeriod.date.asc())
        .all()
    )

    return HistoryResponse(
        domain_id=domain_id,
        kpi_id=kpi_id,
        kpi_name=kpi.kpi_name,
        location_id=location_id,
        location_name=loc.location_name,
        unit=kpi.unit or "",
        target_threshold=kpi.target_threshold,
        higher_is_better=bool(kpi.higher_is_better),
        history=[
            HistoryPoint(
                date=period.date,
                actual_value=fact.actual_value,
                z_score=fact.z_score,
                is_anomaly=bool(fact.is_anomaly),
                status=fact.status or "GREEN",
            )
            for fact, period in rows
        ],
    )

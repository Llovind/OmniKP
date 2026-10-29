"""Unified reporting: target attainment first, statistical deviations separately."""
from datetime import date as Date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import (get_db, DimDomain, DimKPI, DimLocation, DimPeriod, FactKPI,
                      ReadingSource, Submission, DivisionFeedback)
from dependencies import get_validated_domain
from schemas import KPIInfo, LocationNode, HeatmapResponse, HistoryResponse, HistoryPoint
from services.performance import target_status, attainment

router = APIRouter(prefix='/api/v1/domains/{domain_id}', tags=['KPI & Heatmap'],
                   dependencies=[Depends(get_validated_domain)])


def report_query(db, domain_id, dataset='all', division=None):
    query = db.query(FactKPI, DimKPI, DimLocation, DimPeriod, ReadingSource, Submission).join(
        DimKPI, FactKPI.kpi_id == DimKPI.kpi_id).join(
        DimLocation, FactKPI.location_id == DimLocation.location_id).join(
        DimPeriod, FactKPI.period_id == DimPeriod.period_id).outerjoin(
        ReadingSource, ReadingSource.fact_id == FactKPI.fact_id).outerjoin(
        Submission, Submission.submission_id == ReadingSource.submission_id).filter(FactKPI.domain_id == domain_id)
    if dataset == 'submitted':
        query = query.filter(ReadingSource.fact_id.isnot(None))
    elif dataset == 'demo':
        query = query.filter(ReadingSource.fact_id.is_(None))
    if division:
        query = query.filter(ReadingSource.division == division)
    return query


def period_rows(db, domain_id, dataset, division, date):
    query = report_query(db, domain_id, dataset, division)
    day = date.isoformat() if date else query.with_entities(func.max(DimPeriod.date)).scalar()
    rows = query.filter(DimPeriod.date == day).order_by(DimKPI.kpi_archetype, DimKPI.kpi_name).all() if day else []
    return day or '', rows


@router.get('/periods')
def list_periods(domain_id: int, dataset: str = Query('all', pattern='^(all|submitted|demo)$'),
                 division: str | None = None, db: Session = Depends(get_db)):
    return [r[0] for r in report_query(db, domain_id, dataset, division).with_entities(
        DimPeriod.date).distinct().order_by(DimPeriod.date.desc()).all()]


@router.get('/locations', response_model=list[LocationNode])
def list_locations(domain_id: int, db: Session = Depends(get_db)):
    locs = db.query(DimLocation).filter_by(domain_id=domain_id).all()
    nodes = {l.location_id: LocationNode(location_id=l.location_id, location_name=l.location_name,
              location_type=l.location_type, parent_location_id=l.parent_location_id, domain_id=domain_id) for l in locs}
    roots = []
    for node in nodes.values():
        if node.parent_location_id in nodes:
            nodes[node.parent_location_id].children.append(node)
        else:
            roots.append(node)
    return roots


@router.get('/kpis', response_model=list[KPIInfo])
def list_kpis(domain_id: int, db: Session = Depends(get_db)):
    return db.query(DimKPI).filter_by(domain_id=domain_id).order_by(DimKPI.kpi_archetype, DimKPI.kpi_name).all()


@router.get('/heatmap', response_model=HeatmapResponse)
def get_heatmap(domain_id: int, dataset: str = Query('all', pattern='^(all|submitted|demo)$'),
                division: str | None = None, date: Date | None = None, db: Session = Depends(get_db)):
    day, rows = period_rows(db, domain_id, dataset, division, date)
    feedback_counts = dict(db.query(DivisionFeedback.fact_id, func.count(DivisionFeedback.feedback_id))
                           .group_by(DivisionFeedback.fact_id).all())
    locations = {}
    for fact, kpi, loc, period, source, submission in rows:
        if loc.location_id not in locations:
            locations[loc.location_id] = dict(location_id=loc.location_id, location_name=loc.location_name,
                location_type=loc.location_type, parent_location_id=loc.parent_location_id, kpis=[],
                summary=dict(total=0, red=0, yellow=0, green=0))
        status = target_status(fact.actual_value, fact.target_value, kpi.higher_is_better)
        item = locations[loc.location_id]
        item['kpis'].append(dict(fact_id=fact.fact_id, kpi_id=kpi.kpi_id, kpi_name=kpi.kpi_name,
            kpi_archetype=kpi.kpi_archetype, actual_value=fact.actual_value, target_value=fact.target_value,
            z_score=fact.z_score, is_anomaly=fact.is_anomaly, status=status, unit=kpi.unit or '',
            higher_is_better=bool(kpi.higher_is_better), date=period.date,
            division=source.division if source else None, source_file=submission.filename if submission else None,
            source_row=source.source_row if source else None,
            attainment_pct=attainment(fact.actual_value, fact.target_value, kpi.higher_is_better),
            feedback_count=feedback_counts.get(fact.fact_id, 0)))
        item['summary']['total'] += 1
        item['summary'][status.lower()] += 1
    domain = db.query(DimDomain).filter_by(domain_id=domain_id).first()
    return dict(domain_id=domain_id, domain_name=domain.domain_name, date=day,
                locations=sorted(locations.values(), key=lambda l: l['location_name']))


@router.get('/kpis/{kpi_id}/history', response_model=HistoryResponse)
def get_kpi_history(domain_id: int, kpi_id: int, location_id: int = Query(...),
                    as_of: Date | None = None, db: Session = Depends(get_db)):
    kpi = db.query(DimKPI).filter_by(domain_id=domain_id, kpi_id=kpi_id).first()
    loc = db.query(DimLocation).filter_by(domain_id=domain_id, location_id=location_id).first()
    if not kpi or not loc:
        raise HTTPException(404, 'KPI or location not found in this domain.')
    query = db.query(FactKPI, DimPeriod).join(DimPeriod).filter(
        FactKPI.domain_id == domain_id, FactKPI.kpi_id == kpi_id, FactKPI.location_id == location_id)
    if as_of:
        query = query.filter(DimPeriod.date <= as_of.isoformat())
    rows = query.order_by(DimPeriod.date.desc()).limit(30).all()[::-1]
    return HistoryResponse(domain_id=domain_id, kpi_id=kpi_id, kpi_name=kpi.kpi_name,
        location_id=location_id, location_name=loc.location_name, unit=kpi.unit or '',
        target_threshold=rows[-1][0].target_value if rows else kpi.target_threshold,
        higher_is_better=kpi.higher_is_better,
        history=[HistoryPoint(date=p.date, actual_value=f.actual_value, z_score=f.z_score,
                  is_anomaly=f.is_anomaly, target_value=f.target_value,
                  status=target_status(f.actual_value, f.target_value, kpi.higher_is_better)) for f, p in rows])

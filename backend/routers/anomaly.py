"""Business exceptions for the selected report period."""
from datetime import date as Date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_validated_domain
from routers.kpi import period_rows
from services.performance import target_status

router = APIRouter(prefix='/api/v1/domains/{domain_id}', tags=['Performance exceptions'],
                   dependencies=[Depends(get_validated_domain)])


@router.get('/anomalies')
def get_current_anomalies(domain_id: int, dataset: str = Query('all', pattern='^(all|submitted|demo)$'),
                          division: str | None = None, date: Date | None = None, db: Session = Depends(get_db)):
    day, rows = period_rows(db, domain_id, dataset, division, date)
    items = []
    for fact, kpi, loc, period, source, _ in rows:
        if target_status(fact.actual_value, fact.target_value, kpi.higher_is_better) != 'RED':
            continue
        items.append(dict(fact_id=fact.fact_id, kpi_id=kpi.kpi_id, kpi_name=kpi.kpi_name,
            kpi_archetype=kpi.kpi_archetype, location_id=loc.location_id, location_name=loc.location_name,
            actual_value=fact.actual_value, target_value=fact.target_value, z_score=fact.z_score,
            status='RED', unit=kpi.unit, date=period.date, division=source.division if source else None,
            anomaly_reason='Below target' if kpi.higher_is_better else 'Above allowed limit'))
    items.sort(key=lambda x: abs(x['actual_value'] - x['target_value']) / max(abs(x['target_value']), 1e-9), reverse=True)
    return dict(domain_id=domain_id, date=day, total_anomalies=len(items), anomalies=items)

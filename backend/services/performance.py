"""Target attainment is independent of statistical deviation."""
import math
from datetime import date, timedelta

from sqlalchemy import func
from database import DimPeriod, FactKPI


def target_status(actual, target, higher):
    if target is None:
        return "YELLOW"
    met = actual >= target if higher else actual <= target
    return "GREEN" if met else "RED"


def attainment(actual, target, higher):
    if target is None:
        return None
    denominator = target if higher else actual
    if denominator == 0:
        return 100.0 if actual == target else None
    return round((actual / target if higher else target / actual) * 100, 2)


def latest_date(db, domain_id):
    return db.query(func.max(DimPeriod.date)).join(
        FactKPI, FactKPI.period_id == DimPeriod.period_id
    ).filter(FactKPI.domain_id == domain_id).scalar()


def recompute_series(db, domain_id, kpi_id, location_id):
    """Causal 30-calendar-day baseline; also repairs later points after backfills."""
    rows = db.query(FactKPI, DimPeriod.date).join(DimPeriod).filter(
        FactKPI.domain_id == domain_id, FactKPI.kpi_id == kpi_id,
        FactKPI.location_id == location_id,
    ).order_by(DimPeriod.date).all()
    history = []
    for fact, day in rows:
        cutoff = (date.fromisoformat(day) - timedelta(days=30)).isoformat()
        baseline = [value for prev_day, value in history if cutoff <= prev_day < day]
        fact.z_score = None
        fact.is_anomaly = False
        fact.anomaly_reason = "insufficient_historical_data"
        if len(baseline) >= 10:
            mean = sum(baseline) / len(baseline)
            std = math.sqrt(sum((x - mean) ** 2 for x in baseline) / len(baseline))
            if std > 1e-9:
                fact.z_score = round((fact.actual_value - mean) / std, 4)
                fact.is_anomaly = abs(fact.z_score) > 2
                fact.anomaly_reason = f"Z-score {fact.z_score:.2f}" if fact.is_anomaly else None
            else:
                fact.anomaly_reason = "constant_baseline"
        # Stored color now represents the business target. Anomalies remain separate.
        fact.status = target_status(fact.actual_value, fact.target_value, fact.kpi.higher_is_better)
        history.append((day, fact.actual_value))

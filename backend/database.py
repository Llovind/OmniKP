"""
database.py — SQLAlchemy models and database initialization for OmniKPI / PlantIntel.

Star Schema:
    dim_domain   (tenant isolation: 1=telco, 2=petrochemical)
    dim_kpi      (KPI definitions, sourced from ISO 22400 + TM Forum / industry practice)
    dim_location (adjacency list, hierarchy-agnostic; rollup via WITH RECURSIVE CTE)
    dim_period   (daily time periods)
    fact_kpi     (central fact table with pre-computed Z-scores and anomaly flags)
    shift_logs   (operational log entries for RCA retrieval)

Full-text search:
    shift_logs_fts — SQLite FTS5 virtual table, auto-synced via INSERT trigger.
    Query pattern: FTS5 MATCH for text relevance + metadata filter on domain_id/location_id.

All FastAPI routes enforce domain_id via Depends() at router level — see main.py.
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    ForeignKey, Text, text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ─── Engine ──────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'omnikpi.db')}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + threading
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Dimension Tables ─────────────────────────────────────────────────────────

class DimDomain(Base):
    """
    Tenant isolation table.
    domain_id 1 = Telecommunications (ITASE track)
    domain_id 2 = Petrochemical       (CALIBER track)
    All routes enforce domain_id via FastAPI Depends() — never filter manually per-endpoint.
    """
    __tablename__ = "dim_domain"

    domain_id   = Column(Integer, primary_key=True)
    domain_name = Column(String(100), nullable=False)
    domain_code = Column(String(50),  nullable=False)   # "telco" | "petrochemical"


class DimKPI(Base):
    """
    KPI definitions across both domains.
    kpi_archetype maps each KPI to one of 5 structural archetypes derived from two
    independent standards: ISO 22400 (petrochemical) and TM Forum / industry practice (telco).
    This shared archetype taxonomy enables cross-domain queries via a single schema.
    """
    __tablename__ = "dim_kpi"

    kpi_id              = Column(Integer, primary_key=True, autoincrement=True)
    kpi_name            = Column(String(200), nullable=False)
    kpi_archetype       = Column(String(50),  nullable=False)
    # Archetypes: Availability | Performance | Quality | Reliability | Composite
    domain_id           = Column(Integer, ForeignKey("dim_domain.domain_id"), nullable=False)
    formula_description = Column(Text)
    unit                = Column(String(50))
    target_threshold    = Column(Float)
    higher_is_better    = Column(Boolean, default=True)
    source_standard     = Column(String(200))   # "ISO 22400" | "TM Forum/Industry" | "Domain Practice"

    domain = relationship("DimDomain")


class DimLocation(Base):
    """
    Adjacency list (self-referencing FK) — hierarchy-agnostic.
    Rollup aggregation uses WITH RECURSIVE CTE anchored at leaf nodes
    (anchor: NOT EXISTS child) to prevent double-counting at all hierarchy levels.

    Telco:         Nasional → Regional → Witel → District
    Petrochemical: Plant → Unit
    """
    __tablename__ = "dim_location"

    location_id        = Column(Integer, primary_key=True, autoincrement=True)
    location_name      = Column(String(200), nullable=False)
    location_type      = Column(String(50),  nullable=False)   # national | regional | witel | district | plant | unit
    parent_location_id = Column(Integer, ForeignKey("dim_location.location_id"), nullable=True)
    domain_id          = Column(Integer, ForeignKey("dim_domain.domain_id"),     nullable=False)

    parent   = relationship("DimLocation", remote_side="DimLocation.location_id", backref="children")
    domain   = relationship("DimDomain")


class DimPeriod(Base):
    """Daily time granularity. One reading per KPI per location per day."""
    __tablename__ = "dim_period"

    period_id    = Column(Integer, primary_key=True, autoincrement=True)
    date         = Column(String(10), nullable=False)    # ISO 8601 date: YYYY-MM-DD
    shift        = Column(String(20), nullable=False, default="Daily")
    period_label = Column(String(50), nullable=False)    # "2026-07-27 Daily"


# ─── Fact Table ───────────────────────────────────────────────────────────────

class FactKPI(Base):
    """
    Central fact table.

    Z-score computation:
        z = (actual_value - historical_mean) / historical_std
        Anomaly threshold: |Z| > 2.0
        Minimum sample guard: is_anomaly = False if < 10 historical points exist
            (returns reason = "insufficient_historical_data")

    Z-scores stored here are pre-computed at seed time over a 30-day window.
    The anomaly detection endpoint (Step 2) recomputes dynamically from this table.
    Confidence scores in RCA Agent are derived from Z-score — not LLM-generated.
    """
    __tablename__ = "fact_kpi"

    fact_id        = Column(Integer, primary_key=True, autoincrement=True)
    kpi_id         = Column(Integer, ForeignKey("dim_kpi.kpi_id"),          nullable=False)
    location_id    = Column(Integer, ForeignKey("dim_location.location_id"),nullable=False)
    period_id      = Column(Integer, ForeignKey("dim_period.period_id"),     nullable=False)
    domain_id      = Column(Integer, ForeignKey("dim_domain.domain_id"),     nullable=False)
    actual_value   = Column(Float, nullable=False)
    target_value   = Column(Float)
    z_score        = Column(Float)
    is_anomaly     = Column(Boolean, default=False)
    anomaly_reason = Column(String(200))      # "Z-score -22.63" | "insufficient_historical_data" | None
    status         = Column(String(10))       # "GREEN" | "YELLOW" | "RED"

    kpi      = relationship("DimKPI")
    location = relationship("DimLocation")
    period   = relationship("DimPeriod")
    domain   = relationship("DimDomain")


# ─── Shift Logs (RCA Retrieval) ───────────────────────────────────────────────

class ShiftLog(Base):
    """
    Operational shift log entries for RCA context retrieval.

    Full-text search backed by SQLite FTS5 (shift_logs_fts virtual table).
    Auto-synced via INSERT trigger created in init_db().
    Query pattern in RCA Agent:
        SELECT * FROM shift_logs_fts
        WHERE shift_logs_fts MATCH :query
          AND domain_id = :domain_id
          AND location_id = :location_id
        ORDER BY rank
        LIMIT 5;
    Result rowids join back to shift_logs for full metadata.
    """
    __tablename__ = "shift_logs"

    log_id      = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("dim_location.location_id"), nullable=False)
    domain_id   = Column(Integer, ForeignKey("dim_domain.domain_id"),     nullable=False)
    timestamp   = Column(String(30), nullable=False)   # "YYYY-MM-DD HH:MM:SS"
    log_text    = Column(Text, nullable=False)
    kpi_id      = Column(Integer, ForeignKey("dim_kpi.kpi_id"), nullable=True)

    location = relationship("DimLocation")
    domain   = relationship("DimDomain")


# ─── Initialization ───────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all ORM-managed tables (idempotent).
    Also creates the FTS5 virtual table and auto-sync trigger for shift_logs.
    Safe to call on every app startup.
    """
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # FTS5 virtual table: standalone (not content table) with UNINDEXED metadata
        # columns so we can filter by domain_id/location_id after a text MATCH.
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS shift_logs_fts
            USING fts5(
                log_text,
                location_id UNINDEXED,
                domain_id   UNINDEXED,
                log_id      UNINDEXED
            )
        """))

        # Trigger: auto-insert into FTS5 index on every shift_logs INSERT.
        # This keeps the FTS5 index in sync without manual population.
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS shift_logs_ai
            AFTER INSERT ON shift_logs
            BEGIN
                INSERT INTO shift_logs_fts(rowid, log_text, location_id, domain_id, log_id)
                VALUES (NEW.log_id, NEW.log_text, NEW.location_id, NEW.domain_id, NEW.log_id);
            END
        """))

        conn.commit()


def get_db():
    """
    FastAPI dependency injection.
    Yields a SQLAlchemy session and ensures it is closed after request completion.
    All routers that need DB access declare: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
main.py — OmniKPI FastAPI application entrypoint.

Architecture: Monorepo, frontend-backend decoupled via REST API (SPA + FastAPI).
Domain isolation: all routes enforce domain_id via Depends() at router level.
Tech stack: Python + FastAPI + SQLite (SQLAlchemy Star Schema).

Run dev server:
    uvicorn main:app --reload --port 8000

API docs (auto-generated):
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import DimDomain, get_db, init_db, SessionLocal
from dotenv import load_dotenv

load_dotenv()

from routers.anomaly import router as anomaly_router
from routers.harvest import router as harvest_router
from routers.kpi import router as kpi_router
from routers.rca import router as rca_router
from routers.submissions import router as submissions_router


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables (and FTS5 trigger) on startup. Safe to call on every start."""
    init_db()
    with SessionLocal() as db:
        if not db.query(DimDomain).filter_by(domain_id=1).first():
            db.add(DimDomain(domain_id=1, domain_name="Telecommunications", domain_code="digital_infra"))
            db.commit()
    yield


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="OmniKPI — Telco KPI Intelligence API",
    description=(
        "Telecommunications KPI Intelligence Platform — Tri-Agent System\n\n"
        "**UN SDG 9 Mandate:** Resilient Telecommunications Infrastructure\n\n"
        "**Domain:** `1` = Telecommunications (SDG 9.c), ITASE 7.0\n\n"
        "**Workflow:** Division reports → reviewed mappings → unified target dashboard → division feedback → RCA draft"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ─── CORS ─────────────────────────────────────────────────────────────────────

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(kpi_router)
app.include_router(anomaly_router)
app.include_router(rca_router)
app.include_router(harvest_router)
app.include_router(submissions_router)
from routers.demo import router as demo_router, workspace as demo_workspace
app.include_router(demo_router)
app.mount('/api/demo/workspace', demo_workspace)


# ─── Root Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Liveness probe. Returns app version and status."""
    return {"status": "ok", "version": "0.1.0", "app": "OmniKPI"}


@app.get("/api/v1/domains", tags=["System"])
def list_domains(db: Session = Depends(get_db)):
    """
    List the active telecommunications domain.
    Returns domain_id, domain_name, domain_code for the active telco domain.
    """
    domains = db.query(DimDomain).filter(DimDomain.domain_id == 1).all()
    return [
        {
            "domain_id":   d.domain_id,
            "domain_name": d.domain_name,
            "domain_code": d.domain_code,
        }
        for d in domains
    ]


@app.get('/api/v1/ai/status', tags=['System'])
def ai_status():
    from agents.harvester import OPENROUTER_API_KEY, LLM_MODEL
    return {'configured': bool(OPENROUTER_API_KEY),
            'model': LLM_MODEL if OPENROUTER_API_KEY else None}

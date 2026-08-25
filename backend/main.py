"""
main.py — OmniKPI / PlantIntel FastAPI application entrypoint.

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

from database import DimDomain, get_db, init_db
from dotenv import load_dotenv

from routers.anomaly import router as anomaly_router
from routers.harvest import router as harvest_router
from routers.kpi import router as kpi_router
from routers.rca import router as rca_router

load_dotenv()


# ─── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables (and FTS5 trigger) on startup. Safe to call on every start."""
    init_db()
    yield


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="OmniKPI — SDG 9 Infrastructure Intelligence API",
    description=(
        "Agentic Infrastructure & Industrial KPI Intelligence Platform — Tri-Agent System\n\n"
        "**UN SDG 9 Mandate:** Resilient Infrastructure & Sustainable Industrialization\n\n"
        "**Domains:** `1` = Digital Infrastructure (SDG 9.c), `2` = Sustainable Industry (SDG 9.4)\n\n"
        "**Agents:** Harvester (ETL) · ML Heatmap Engine · RCA Diagnostic Agent (LLM-grounded)"
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


# ─── Root Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Liveness probe. Returns app version and status."""
    return {"status": "ok", "version": "0.1.0", "app": "OmniKPI/PlantIntel"}


@app.get("/api/v1/domains", tags=["System"])
def list_domains(db: Session = Depends(get_db)):
    """
    List available domains. Used by the frontend domain switcher.
    Returns domain_id, domain_name, domain_code for all seeded domains.
    """
    domains = db.query(DimDomain).all()
    return [
        {
            "domain_id":   d.domain_id,
            "domain_name": d.domain_name,
            "domain_code": d.domain_code,
        }
        for d in domains
    ]

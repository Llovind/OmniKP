"""Isolated synthetic workspace; existing intake and query services are reused."""
import asyncio
import json
import hashlib
from pathlib import Path
from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, DimDomain, Submission, get_db
from services.intake import stage, confirm, plain_mapping

ROOT = Path(__file__).resolve().parents[2]
engine = create_engine('sqlite:///' + (ROOT/'backend/omnikpi-demo.db').as_posix(), connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
lock = asyncio.Lock()
router = APIRouter()

def demo_db():
    with Session() as db:
        yield db

workspace = FastAPI()
workspace.dependency_overrides[get_db] = demo_db
from routers.kpi import router as kpi
from routers.anomaly import router as anomaly
from routers.rca import router as rca
from routers.submissions import router as submissions
for route in (kpi, anomaly, rca, submissions):
    workspace.include_router(route)

@router.post('/api/demo/seed')
async def seed(reset: bool = False):
    async with lock:
        fixtures = ROOT/'frontend/public/demo/divisions'
        manifest = json.loads((fixtures/'manifest.json').read_text())
        if any(not (fixtures/e['filename']).exists() for e in manifest):
            raise HTTPException(503, 'The seven demo workbooks are missing.')
        version = hashlib.sha256(b''.join((fixtures/e['filename']).read_bytes() for e in manifest)).hexdigest()[:16]
        Base.metadata.create_all(engine)
        with Session() as existing:
            domain = existing.get(DimDomain, 1)
            reset = reset or bool(domain and domain.domain_code != 'demo-'+version)
        if reset:
            Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        with Session() as db:
            if not db.query(DimDomain).filter_by(domain_id=1).first():
                db.add(DimDomain(domain_id=1, domain_name='Telecommunications', domain_code='demo-'+version))
                db.commit()
            for e in manifest:
                if db.query(Submission).filter_by(division=e['division'], filename=e['filename'], status='confirmed').first():
                    continue
                draft = await stage(db, 1, (fixtures/e['filename']).read_bytes(), e['filename'], e['division'], e['report_date'], e['sheet'], e['header_row'], e['header_depth'], False)
                confirm(db, db.get(Submission, draft['submission_id']), plain_mapping(draft['column_mapping']))
        return {'date':'2026-06-30', 'readings':180, 'synthetic':True}

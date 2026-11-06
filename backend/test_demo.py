import tempfile
import unittest
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import FactKPI, DivisionFeedback
from main import app
from routers import demo
from agents import feedback_rca, harvester

class DemoFlow(unittest.TestCase):
    def test_seed_idempotency_reset_and_no_key_feedback(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = create_engine('sqlite:///'+(Path(temp)/'demo.db').as_posix(), connect_args={'check_same_thread':False})
            session = sessionmaker(bind=engine)
            async def simulate_model(**kwargs):
                context = json.loads(kwargs['messages'][1]['content'])
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({col['header']:col['suggestion'] for col in context})))])
            with patch.object(demo,'engine',engine), patch.object(demo,'Session',session), patch.object(feedback_rca,'OPENROUTER_API_KEY',''), patch.object(harvester,'OPENROUTER_API_KEY','mock'), patch.object(harvester._client.chat.completions,'create',new=AsyncMock(side_effect=simulate_model)) as model:
                client = TestClient(app)
                for path in ['/api/demo/seed','/api/demo/seed','/api/demo/seed?reset=true']:
                    response = client.post(path)
                    self.assertEqual(response.status_code,200,response.text)
                    self.assertEqual(response.json()['ai_reports'],7)
                    with session() as db:
                        self.assertEqual(db.query(FactKPI).count(),180)
                        self.assertGreater(db.query(DivisionFeedback).count(),0)
                view=client.get('/api/demo/workspace/api/v1/domains/1/heatmap?dataset=submitted&date=2026-06-30').json()
                self.assertEqual(sum(len(l['kpis']) for l in view['locations']),180)
                with session() as db:
                    feedback=db.query(DivisionFeedback).first()
                    fact=db.get(FactKPI,feedback.fact_id)
                    response=client.post('/api/demo/workspace/api/v1/domains/1/rca',json={'kpi_id':fact.kpi_id,'location_id':fact.location_id,'fact_id':fact.fact_id})
                    self.assertEqual(response.status_code,503,response.text)
                self.assertEqual(model.await_count,14)
                with patch.object(harvester._client.chat.completions,'create',new=AsyncMock(side_effect=RuntimeError('provider unavailable'))):
                    response=client.post('/api/demo/seed?reset=true')
                    self.assertEqual(response.status_code,503)
                    with session() as db:
                        self.assertEqual(db.query(FactKPI).count(),180)
            engine.dispose()

if __name__ == '__main__':
    unittest.main()

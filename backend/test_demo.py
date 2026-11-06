import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import FactKPI, DivisionFeedback
from main import app
from routers import demo
from agents import feedback_rca

class DemoFlow(unittest.TestCase):
    def test_seed_idempotency_reset_and_no_key_feedback(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = create_engine('sqlite:///'+(Path(temp)/'demo.db').as_posix(), connect_args={'check_same_thread':False})
            session = sessionmaker(bind=engine)
            with patch.object(demo,'engine',engine), patch.object(demo,'Session',session), patch.object(feedback_rca,'OPENROUTER_API_KEY',''):
                client = TestClient(app)
                for path in ['/api/demo/seed','/api/demo/seed','/api/demo/seed?reset=true']:
                    response = client.post(path)
                    self.assertEqual(response.status_code,200,response.text)
                    with session() as db:
                        self.assertEqual(db.query(FactKPI).count(),180)
                        self.assertGreater(db.query(DivisionFeedback).count(),0)
                view=client.get('/api/demo/workspace/api/v1/domains/1/heatmap?dataset=submitted&date=2026-06-30').json()
                self.assertEqual(sum(len(l['kpis']) for l in view['locations']),180)
                with session() as db:
                    feedback=db.query(DivisionFeedback).first()
                    fact=db.get(FactKPI,feedback.fact_id)
                    response=client.post('/api/demo/workspace/api/v1/domains/1/rca',json={'kpi_id':fact.kpi_id,'location_id':fact.location_id,'fact_id':fact.fact_id})
                    self.assertEqual(response.status_code,200,response.text)
                    body=response.json()
                    self.assertEqual(body['evidence_status'],'feedback_available')
                    self.assertIn('ai_invoked',body)
                    self.assertIn('grounding',body)
                    self.assertEqual(body['grounding']['ungrounded_claims'],0)
            engine.dispose()

if __name__ == '__main__':
    unittest.main()

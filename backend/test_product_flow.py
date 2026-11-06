"""Run: python -m unittest test_product_flow -v (isolated DB, no provider calls)."""
import asyncio
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

_temp = tempfile.TemporaryDirectory(prefix='omnikpi-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_temp.name) / 'test.db').as_posix()

from openpyxl import Workbook
from fastapi.testclient import TestClient
from database import (Base, engine, init_db, SessionLocal, DimDomain, FactKPI,
                      DivisionFeedback, DimKPI, DimLocation, DimPeriod, Submission)
from main import app
from agents import feedback_rca
from agents import harvester
from services.intake import read_report


class ProductFlow(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        engine.dispose()
        _temp.cleanup()

    def setUp(self):
        # FTS is not used by the new feedback-based endpoint; reset all ORM data.
        Base.metadata.drop_all(engine)
        init_db()
        with SessionLocal() as db:
            db.add(DimDomain(domain_id=1, domain_name='Telco', domain_code='digital_infra'))
            db.add(DimDomain(domain_id=2, domain_name='Legacy', domain_code='legacy'))
            db.commit()
        self.client = TestClient(app)
        self.client.__enter__()
        self.no_ai = patch.object(feedback_rca, 'OPENROUTER_API_KEY', '')
        self.no_ai.start()

    def tearDown(self):
        self.no_ai.stop()
        self.client.__exit__(None, None, None)

    def stage(self, content, division='Mobile Broadband', day='2026-10-02', filename='input.csv', **extra):
        result = self.client.post('/api/v1/domains/1/submissions/preview',
            files={'file': (filename, content)}, data=dict(division=division, report_date=day, **extra))
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def accept(self, report, mapping=None):
        mapping = mapping or {col: info['target'] for col, info in report['column_mapping'].items()}
        payload = {'mapping': mapping}
        prefix = '/api/v1/domains/1/submissions/' + report['submission_id']
        reviewed = self.client.post(prefix+'/review', json=payload)
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertTrue(reviewed.json()['can_confirm'], reviewed.text)
        confirmed = self.client.post(prefix+'/confirm', json=payload)
        self.assertEqual(confirmed.status_code, 200, confirmed.text)
        return confirmed.json()

    def dashboard(self, **params):
        response = self.client.get('/api/v1/domains/1/heatmap', params={'dataset': 'submitted', **params})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_multiple_divisions_wide_and_rows_unify(self):
        root = Path(__file__).resolve().parents[1] / 'frontend/public/demo'
        first = self.stage((root/'mobile-broadband.csv').read_bytes())
        self.assertEqual(self.dashboard()['locations'], [], 'Preview must not write facts')
        self.assertEqual(self.accept(first)['readings_imported'], 6)
        second = self.stage((root/'fiber-connectivity.csv').read_bytes(), division='Fiber Connectivity')
        self.assertEqual(self.accept(second)['readings_imported'], 4)
        dashboard = self.dashboard()
        cells = [k for l in dashboard['locations'] for k in l['kpis']]
        self.assertEqual(len(cells), 7)
        self.assertEqual({k['division'] for k in cells}, {'Mobile Broadband', 'Fiber Connectivity'})
        self.assertTrue(all(k['source_file'] and k['source_row'] for k in cells))
        self.assertEqual(len(self.dashboard(division='Fiber Connectivity')['locations']), 2)
        periods = self.client.get('/api/v1/domains/1/periods?dataset=submitted').json()
        self.assertEqual(periods, ['2026-10-02', '2026-10-01'])
        self.assertEqual(len(self.dashboard(date='2026-10-01')['locations']), 2)
        self.assertEqual(self.dashboard(date='2026-10-03')['locations'], [], 'No stale carry-forward')
        self.assertEqual(len(self.client.get('/api/v1/domains/1/submissions').json()), 2)
        self.assertEqual(self.client.get('/api/v1/domains/2/heatmap').status_code, 404)

    def test_seven_reconstructed_divisions_reconcile_every_reading(self):
        root = Path(__file__).resolve().parents[1]
        fixtures = root/'frontend/public/demo/divisions'
        manifest = json.loads((fixtures/'manifest.json').read_text())
        expected = json.loads((fixtures/'expected-readings.json').read_text())
        self.assertEqual(sum(r['kpis'] for r in manifest), 90)
        for entry in manifest:
            report = self.stage((fixtures/entry['filename']).read_bytes(), division=entry['division'], day=entry['report_date'], filename=entry['filename'], sheet_name=entry['sheet'], header_row=entry['header_row'])
            self.assertTrue(report['can_confirm'], report['issues'])
            result = self.accept(report)
            self.assertEqual(result['readings_imported'], entry['readings'])
        dashboard = self.dashboard(date='2026-06-30')
        actual = {(k['division'], k['kpi_name'], loc['location_name']): k for loc in dashboard['locations'] for k in loc['kpis']}
        self.assertEqual(len(actual), 180)
        for row in expected:
            cell = actual[(row['division'], row['kpi_name'], row['location_name'])]
            for field in ('actual_value', 'target_value', 'unit', 'date', 'attainment_pct', 'source_file', 'source_row'):
                self.assertEqual(cell[field], row[field])
            meets = row['actual_value'] >= row['target_value'] if row['higher_is_better'] else row['actual_value'] <= row['target_value']
            self.assertEqual(cell['status'], 'GREEN' if meets else 'RED')
        for entry in manifest:
            view = self.dashboard(division=entry['division'])
            self.assertEqual(sum(len(l['kpis']) for l in view['locations']), entry['readings'])
        self.assertEqual(len(self.client.get('/api/v1/domains/1/submissions').json()), 7)

    def test_ai_wide_report_batches_and_partial_fallback(self):
        from services.intake import ai_mapping, suggest_mapping
        columns = [f'Demo {i} | Actual' for i in range(121)]
        report = {'columns': columns, 'rows': [{'values': dict.fromkeys(columns, 95)}]}
        first = {c: 'location:'+c.split('|')[0].strip() for c in columns[:60]}
        last = {columns[-1]: 'location:Demo 120'}
        response = lambda payload: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])
        with patch.object(harvester, 'OPENROUTER_API_KEY', 'test'), patch.object(harvester._client.chat.completions, 'create', new=AsyncMock(side_effect=[response(first), RuntimeError('provider failure'), response(last)])) as call:
            mapping, message, trace = asyncio.run(ai_mapping(report, suggest_mapping(columns)))
        self.assertEqual(call.await_count, 3)
        self.assertEqual(sum(m['method'] == 'llm' for m in mapping.values()), 61)
        self.assertEqual(trace['mode'], 'live')
        self.assertEqual(trace['batches'], 3)
        self.assertEqual(trace['fallback_batches'], 1)
        self.assertIn('1 batch(es) failed and kept local rules', message)
        self.assertEqual(len(mapping), 121)

    def test_validation_pack_failure_exercises(self):
        fixtures = Path(__file__).resolve().parents[1]/'frontend/public/demo/divisions'
        for filename in ['missing-value.xlsx', 'duplicate-reading.xlsx']:
            staged = self.stage((fixtures/filename).read_bytes(), division='ED', day='2026-06-30', filename=filename, header_row=1)
            self.assertFalse(staged['can_confirm'])
            mapping = {c:m['target'] for c,m in staged['column_mapping'].items()}
            response = self.client.post('/api/v1/domains/1/submissions/'+staged['submission_id']+'/confirm',json={'mapping':mapping})
            self.assertEqual(response.status_code,409)
            with SessionLocal() as db:
                self.assertEqual(db.query(FactKPI).count(),0)
        filename = 'changed-headers.xlsx'
        staged = self.stage((fixtures/filename).read_bytes(), division='ED', day='2026-06-30', filename=filename, header_row=1)
        mapping = {c:m['target'] for c,m in staged['column_mapping'].items()}
        mapping.update({'Performance measure':'kpi_name','Observed outcome':'actual_value'})
        self.assertEqual(self.accept(staged,mapping)['readings_imported'],2)

    def test_validation_atomicity_and_manual_mapping(self):
        csv = b'Indicator label,Reading,Target,Location,Unit,Direction\nNew KPI,90,95,North,%,Higher better\nNew KPI,*,95,South,%,Higher better\n'
        report = self.stage(csv)
        mapping = {c: i['target'] for c, i in report['column_mapping'].items()}
        mapping.update({'Indicator label': 'kpi_name', 'Reading': 'actual_value'})
        endpoint = '/api/v1/domains/1/submissions/'+report['submission_id']
        reviewed = self.client.post(endpoint+'/review', json={'mapping': mapping}).json()
        self.assertEqual(reviewed['valid_readings'], 1)
        self.assertEqual(reviewed['invalid_readings'], 1)
        self.assertEqual(self.client.post(endpoint+'/confirm', json={'mapping': mapping}).status_code, 409)
        with SessionLocal() as db:
            self.assertEqual(db.query(FactKPI).count(), 0)
            self.assertEqual(db.query(DimKPI).count(), 0)

    def test_mapping_memory_and_duplicates(self):
        csv = b'KPI,Actual,Target,Location,Unit,Direction\nCustom KPI,90,95,North,%,Higher better\n'
        first = self.stage(csv)
        self.accept(first)
        duplicate = self.client.post('/api/v1/domains/1/submissions/preview',
            files={'file': ('input.csv', csv)}, data={'division': 'Mobile Broadband', 'report_date': '2026-10-02'})
        self.assertEqual(duplicate.status_code, 422)
        next_report = self.stage(csv, day='2026-10-03')
        self.assertTrue(all(m['method'] == 'approved_memory' for m in next_report['column_mapping'].values()))
        self.accept(next_report)
        cross_division = self.stage(csv, division='Core Network')
        self.assertEqual(cross_division['conflict_count'], 1)
        # A changed layout is not mistaken for an approved template.
        changed = self.stage(csv.replace(b'Actual', b'Measured reading'), day='2026-10-04')
        self.assertFalse(any(m['method'] == 'approved_memory' for m in changed['column_mapping'].values()))
        # Case/spacing differences cannot bypass collision detection.
        altered = self.stage(csv.replace(b'North', b' north '), division='Another division')
        self.assertEqual(altered['conflict_count'], 1)

    def test_opt_in_ai_uses_samples_and_requires_review(self):
        proposed = {'Metric label': 'kpi_name', 'Observed figure': 'actual_value',
                    'Limit': 'target_value', 'Area name': 'location_name', 'Unit': 'unit', 'Direction': 'higher_is_better'}
        fake = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(proposed)))])
        with patch.object(harvester, 'OPENROUTER_API_KEY', 'test'), patch.object(
                harvester._client.chat.completions, 'create', new_callable=AsyncMock, return_value=fake) as mock:
            report = self.stage(b'Metric label,Observed figure,Limit,Area name,Unit,Direction\nSynthetic metric,90,95,North,%,Higher better\n', use_ai='true')
            mock.assert_awaited_once()
            self.assertIn('Synthetic metric', mock.call_args.kwargs['messages'][1]['content'])
            self.assertTrue(all(v['method'] == 'llm' for v in report['column_mapping'].values()))
            self.assertEqual(self.dashboard()['locations'], [])
            self.assertEqual(self.accept(report)['readings_imported'], 1)

    def test_target_direction_and_zero(self):
        report = self.stage(b'KPI,Actual,Target,Location,Unit,Direction\nLatency demo,65,50,North,ms,Lower better\nAvailability demo,95,99,North,%,Higher better\nZero incidents,0,0,North,count,Lower better\n')
        self.accept(report)
        cells = {k['kpi_name']: k for l in self.dashboard()['locations'] for k in l['kpis']}
        self.assertEqual(cells['Latency demo']['status'], 'RED')
        self.assertEqual(cells['Availability demo']['status'], 'RED')
        self.assertEqual(cells['Zero incidents']['status'], 'GREEN')
        self.assertEqual(cells['Zero incidents']['attainment_pct'], 100)
        self.assertIsNone(cells['Latency demo']['z_score'])

    def test_feedback_is_exact_and_missing_feedback_never_calls_llm(self):
        report = self.stage(b'KPI,Actual,Target,Location,Unit,Direction\nExample availability,90,99,North,%,Higher better\nExample latency,65,50,North,ms,Lower better\n')
        self.accept(report)
        cells = self.dashboard()['locations'][0]['kpis']
        first, second = cells[0], cells[1]
        payload = lambda c: dict(kpi_id=c['kpi_id'], location_id=self.dashboard()['locations'][0]['location_id'], fact_id=c['fact_id'])
        with patch.object(feedback_rca._client.chat.completions, 'create', new_callable=AsyncMock) as mock:
            no_evidence = self.client.post('/api/v1/domains/1/rca', json=payload(first)).json()
            self.assertEqual(no_evidence['evidence_status'], 'awaiting_feedback')
            mock.assert_not_called()
        response = self.client.post('/api/v1/domains/1/feedback', json={
            'fact_id': first['fact_id'], 'explanation': 'Synthetic division reports a damaged link.',
            'corrective_action': 'Inspect the link and report findings.'})
        self.assertEqual(response.status_code, 200, response.text)
        feedback_id = response.json()['feedback_id']
        answer = self.client.post('/api/v1/domains/1/rca', json=payload(first)).json()
        self.assertEqual(answer['cited_feedback_ids'], [feedback_id])
        other = self.client.post('/api/v1/domains/1/rca', json=payload(second)).json()
        self.assertEqual(other['evidence_status'], 'awaiting_feedback')
        # Reject fabricated source references instead of displaying an unsupported AI draft.
        fake = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            'root_cause': 'Invented explanation [F999]', 'prescriptive_action': 'Do something',
            'cited_feedback_ids': [999]})))])
        with patch.object(feedback_rca, 'OPENROUTER_API_KEY', 'test'), patch.object(
                feedback_rca._client.chat.completions, 'create', new_callable=AsyncMock, return_value=fake):
            answer = self.client.post('/api/v1/domains/1/rca', json=payload(first)).json()
            self.assertNotIn('Invented explanation', answer['root_cause'])
            self.assertIn('invalid citations', answer['llm_model'])

    def test_xlsx_multilevel_headers_and_excel_percent_scale(self):
        book = Workbook()
        sheet = book.active
        sheet.title = 'Report'
        sheet.append(['Synthetic report'])
        sheet.append(['KPI', 'Unit', 'Direction', 'Target', 'North', None, 'South', None])
        sheet.append([None, None, None, None, 'Actual', 'ACH', 'Actual', 'ACH'])
        sheet.append(['Availability test', '%', 'Higher better', .995, .96, .965, .999, 1.004])
        for col in (4, 5, 6, 7, 8):
            sheet.cell(4, col).number_format = '0.00%'
        output = io.BytesIO()
        book.save(output)
        report = self.stage(output.getvalue(), filename='report.xlsx', sheet_name='Report', header_row=2, header_depth=2)
        self.accept(report)
        values = [k['actual_value'] for l in self.dashboard()['locations'] for k in l['kpis']]
        self.assertEqual(values, [96, 99.9])
        self.assertEqual(report['column_mapping']['North | ACH']['target'], 'ignore')

    def test_causal_statistics_and_backfilled_dates(self):
        header = 'KPI,Actual,Target,Location,Unit,Direction,Date\n'
        records = ''.join(f'History KPI,{90+i%3},99,North,%,Higher better,2026-09-{i+1:02d}\n' for i in range(12))
        self.accept(self.stage((header+records).encode()))
        with SessionLocal() as db:
            facts = db.query(FactKPI).join(DimPeriod).order_by(DimPeriod.date).all()
            self.assertIsNone(facts[9].z_score)
            self.assertIsNotNone(facts[10].z_score)
            self.assertTrue(all(f.status == 'RED' for f in facts))


if __name__ == '__main__':
    unittest.main()

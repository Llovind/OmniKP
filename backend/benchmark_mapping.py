"""Synthetic mapping benchmark; never reads KPI_data or uses the application DB."""
import argparse
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import time


def cases():
    fields = ['kpi_name', 'actual_value', 'target_value', 'location_name', 'unit', 'higher_is_better', 'date']
    layouts = [
        ('standard', ['KPI', 'Actual', 'Target', 'Location', 'Unit', 'Direction', 'Date']),
        ('indonesian', ['Indikator', 'Realisasi', 'Nilai target', 'Lokasi', 'Satuan', 'Arah', 'Tanggal']),
        ('unfamiliar', ['Service measure', 'Observed result', 'Required minimum', 'Reporting area', 'Measurement scale', 'Desired trend', 'Observation day']),
        ('reordered', ['Observation day', 'Reporting area', 'Service measure', 'Desired trend', 'Required minimum', 'Observed result', 'Measurement scale']),
    ]
    for name, headers in layouts:
        order = [6, 3, 0, 5, 2, 1, 4] if name == 'reordered' else list(range(7))
        truth = dict(zip(headers, [fields[i] for i in order]))
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(headers)
        for i in range(100):
            values = ['Synthetic service availability', 94 + i % 6, 99, f'Synthetic site {i:03}', '%', 'Higher better', '2026-10-02']
            writer.writerow([values[j] for j in order])
        yield name, stream.getvalue().encode(), truth, 100
    headers = ['KPI', 'Target', 'Unit', 'Direction', 'Date', 'North | Actual', 'North | ACH', 'South | Actual', 'South | ACH']
    truth = dict(zip(headers, ['kpi_name', 'target_value', 'unit', 'higher_is_better', 'date', 'location:North', 'ignore', 'location:South', 'ignore']))
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(headers)
    for i in range(50):
        writer.writerow([f'Synthetic metric {i}', 99, '%', 'Higher better', '2026-10-02', 95, 96, 99, 100])
    yield 'wide_with_achievement', stream.getvalue().encode(), truth, 100


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-ai', action='store_true', help='Send only generated synthetic headers/samples to configured provider')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--output', default='evidence/mapping-benchmark.json')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    with tempfile.TemporaryDirectory(prefix='omnikpi-benchmark-') as tmp:
        os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(tmp) / 'benchmark.db').as_posix()
        from fastapi.testclient import TestClient
        from database import engine
        from main import app
        from agents.harvester import LLM_MODEL
        results = []
        with TestClient(app) as client:
            for mode in (['rules', 'ai'] if args.live_ai else ['rules']):
                for name, content, truth, expected in cases():
                    for repeat in range(args.repeats):
                        division = f'Benchmark {mode} {name} {repeat}'
                        start = time.perf_counter()
                        response = client.post('/api/v1/domains/1/submissions/preview', files={'file': (name+'.csv', content)}, data={'division': division, 'report_date': '2026-10-02', 'use_ai': str(mode == 'ai').lower()})
                        response.raise_for_status()
                        staged = response.json()
                        preview_seconds = time.perf_counter() - start
                        proposals = staged['column_mapping']
                        errors = [{'column': c, 'expected': t, 'proposed': proposals[c]['target']} for c, t in truth.items() if proposals[c]['target'] != t]
                        prefix = '/api/v1/domains/1/submissions/' + staged['submission_id']
                        started = time.perf_counter()
                        review = client.post(prefix+'/review', json={'mapping': truth})
                        review.raise_for_status()
                        # Each case uses a fresh domain dataset to prevent inter-case fact conflicts.
                        confirmed = client.post(prefix+'/confirm', json={'mapping': truth})
                        confirmed.raise_for_status()
                        count = confirmed.json()['readings_imported']
                        assert count == expected, (name, count, expected)
                        active = [c for c, t in truth.items() if t != 'ignore']
                        results.append(dict(case=name, mode=mode, repeat=repeat, columns=len(truth), correct=len(truth)-len(errors), corrections_required=len(errors), active_columns=len(active), active_correct=sum(proposals[c]['target'] == truth[c] for c in active), llm_columns=sum(v['method'] == 'llm' for v in proposals.values()), preview_seconds=round(preview_seconds, 4), reviewed_import_seconds=round(time.perf_counter()-started, 4), imported_readings=count, errors=errors))
                        print(f'{mode}/{name}/{repeat}: {len(truth)-len(errors)}/{len(truth)} columns; {preview_seconds:.2f}s preview', flush=True)
                        from database import Base, init_db, SessionLocal, DimDomain
                        Base.metadata.drop_all(engine)
                        init_db()
                        with SessionLocal() as db:
                            db.add(DimDomain(domain_id=1, domain_name='Telco', domain_code='digital_infra'))
                            db.commit()
        engine.dispose()
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({'dataset': 'Synthetic v1, 5 layouts, 100 readings each; author-labelled, not independently adjudicated or held-out', 'model': LLM_MODEL if args.live_ai else None, 'human_review_seconds': None, 'manual_consolidation_seconds': None, 'limitations': ['Ground-truth mappings applied automatically; correction counts are mapping differences, not observed human edits.', 'Timing excludes human review and manual Excel work; no human time-saving claim.', 'Rules are a baseline; AI-labelled runs with zero LLM columns are provider fallback, not AI success.', 'CSV layouts only; complex real workbooks and mapping-memory benefits not evaluated.'], 'results': results}, indent=2), encoding='utf-8')
        print(f'Results: {output}')


if __name__ == '__main__':
    run()

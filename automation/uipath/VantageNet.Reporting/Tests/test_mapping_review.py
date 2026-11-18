"""Actual UiPath workflow executions against synthetic HTTP contract responses. No live AI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parents[1]
from cli_support import CLI
OUT = ROOT / 'Output' / 'sprint2-tests' / uuid.uuid4().hex
requests = []
mode = 'valid'


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        assert self.path.endswith('/synthetic-sprint2/review'), self.path
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert payload == {'mapping': {'KPI': 'kpi_name', 'Value': 'actual_value', 'City': 'location_name'}, 'default_direction': None}
        requests.append({'path': self.path, 'payload': payload, 'mode': mode})
        self.send_response(503 if mode == 'http503' else 200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        data = {'can_confirm': mode != 'invalid', 'issues': [{'message': 'invalid reading'}] if mode == 'invalid' else [],
                'conflicts': [{'message': 'existing reading'}] if mode == 'conflict' else [], 'conflict_count': 1 if mode == 'conflict' else 0}
        self.wfile.write(b'{}' if mode == 'malformed' else json.dumps(data).encode())


def run(manifest, base, decision='', label='prepare'):
    args = [str(CLI), 'rpa', 'run', '--file-path', 'ReviewMapping.cs', '--project-dir', str(ROOT),
            '--profile', 'vantagenet-local-noauth', '--skip-build', '--output', 'json',
            '--input-arguments', f'manifestPath={manifest}', '--input-arguments', f'baseUrl={base}']
    if decision:
        args += ['--input-arguments', f'decisionPath={decision}']
    env = {**os.environ, 'UIPATH_CLI_DISABLE_AUTOINSTALL': 'true', 'UIPATH_CLI_DISABLE_VERSION_SYNC': 'true'}
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    (OUT / f'{label}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    return result


def main():
    global mode
    OUT.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    summary = []
    try:
        for name, action, response_mode, expected in [
            ('approval', 'approve', 'valid', 'mapping_approved_confirm_disabled'),
            ('correction', 'correct', 'valid', 'correction_validated_needs_approval'),
            ('rejection', 'reject', 'valid', 'rejected'),
            ('invalid', 'approve', 'invalid', 'mapping_invalid'),
            ('conflict', 'approve', 'conflict', 'mapping_invalid'),
            ('http503', 'approve', 'http503', 'review_http_failed'),
            ('malformed', 'approve', 'malformed', 'review_failed'),
            ('stale', 'approve', 'valid', None),
            ('missing-column', 'approve', 'valid', 'review_failed'),
        ]:
            folder = OUT / name
            folder.mkdir(exist_ok=True)
            preview = {'submission_id': 'synthetic-sprint2', 'columns': ['KPI', 'Value', 'City'],
                       'column_mapping': {'KPI': {'target': 'kpi_name', 'reason': 'KPI header'},
                                          'Value': {'target': 'ignore', 'reason': 'uncertain'},
                                          'City': {'target': 'location_name', 'reason': 'city sample'}},
                       'raw_preview': [{'KPI': '<script>bad()</script>', 'Value': 4, 'City': 'Synthetic City'}],
                       'can_confirm': False, 'issues': [], 'conflicts': []}
            raw = json.dumps(preview)
            (folder / 'preview.json').write_text(raw)
            manifest = folder / 'manifest.json'
            manifest.write_text(json.dumps({'run_id': name, 'submission_id': 'synthetic-sprint2', 'filename': 'synthetic.csv', 'division': 'ED',
                                            'report_date': '2026-06-30', 'confirmed': False, 'state': 'awaiting_human_review'}))
            prepared = run(manifest, base, label=f'{name}-prepare')
            assert prepared.returncode == 0 and '"hasErrors": false' in prepared.stdout, prepared.stdout[-1500:]
            html = (folder / 'mapping-review.html').read_text(encoding='utf-8')
            assert 'KPI header' in html and 'Synthetic City' in html and '<script>bad()</script>' not in html
            d = {'run_id': name, 'submission_id': 'synthetic-sprint2', 'preview_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                 'reviewer': 'synthetic-test-reviewer', 'reason': 'Automated transport test, not a human approval', 'decision': action,
                 'mapping': {'KPI': 'kpi_name', 'Value': 'actual_value', 'City': 'location_name'}, 'default_direction': None}
            if name == 'stale':
                d['submission_id'] = 'wrong'
            if name == 'missing-column':
                del d['mapping']['City']
            decision = folder / 'decision.json'
            decision.write_text(json.dumps(d))
            mode = response_mode
            before = len(requests)
            applied = run(manifest, base, str(decision), label=f'{name}-apply')
            files = list((folder / 'reviews').glob('*/result.json'))
            if name == 'missing-column':
                # Business-rule validation must fail before HTTP. A faulted runtime
                # may omit its result archive; do not mistake that for authorization.
                assert applied.returncode != 0 and 'Mapping must contain every original column exactly once' in applied.stdout
                assert not list((folder / 'reviews').glob('*/review-payload.json'))
                assert not list(folder.glob('confirm*.json'))
                for f in files:
                    result = json.loads(f.read_text())
                    assert result['state'] == 'review_failed' and not result['confirm_authorized'] and not result['confirmed']
            elif expected is None:
                assert applied.returncode != 0 and not files
            else:
                result = json.loads(files[0].read_text())
                assert result['state'] == expected and result['confirm_authorized'] is False and result['confirmed'] is False, result
                assert (applied.returncode != 0) == (name in ('http503', 'malformed', 'missing-column'))
            assert len(requests) - before == (0 if name in ('rejection', 'stale', 'missing-column') else 1)
            if name == 'approval':
                replay = run(manifest, base, str(decision), label='approval-replay')
                assert replay.returncode == 0 and len(requests) == before + 1
                rejected = {**d, 'decision': 'reject'}
                rejection_file = folder / 'rejection.json'
                rejection_file.write_text(json.dumps(rejected))
                assert run(manifest, base, str(rejection_file), label='approval-then-reject').returncode == 0
                assert run(manifest, base, str(decision), label='rejected-approval-replay').returncode != 0
                assert len(requests) == before + 1
            if name == 'invalid':
                assert run(manifest, base, label='invalid-reopen').returncode == 0
                assert 'invalid reading' in (folder / 'mapping-review.html').read_text(encoding='utf-8')
            summary.append({'case': name, 'passed': True, 'expected_state': expected})
            print(name, 'passed', flush=True)
    finally:
        server.shutdown()
        (OUT / 'summary.json').write_text(json.dumps({'synthetic_transport_only': True, 'tests': summary, 'requests': requests}, indent=2))


if __name__ == '__main__':
    main()

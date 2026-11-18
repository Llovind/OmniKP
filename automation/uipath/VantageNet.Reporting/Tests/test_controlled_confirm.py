"""Synthetic HTTP tests of actual UiPath confirm workflow. All approvals are TEST FIXTURES."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Output' / ('c3-' + uuid.uuid4().hex[:8])
OUT.mkdir(parents=True)
from cli_support import CLI
mode = ''
committed = False
posts = []
payload = {'mapping': {'KPI': 'kpi_name', 'Value': 'actual_value'}, 'default_direction': None}
valid = dict(can_confirm=True, issues=[], conflicts=[], conflict_count=0, valid_readings=26)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        try:
            self.wfile.write(json.dumps(data).encode())
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        if self.path == '/_development/instance':
            self.send(dict(disposable=True, instance_id='synthetic-test-instance'))
        else:
            assert self.path == '/api/v1/domains/1/submissions/synthetic-test'
            self.send(dict(submission_id='synthetic-test', status='confirmed' if committed else 'draft', division='ED',
                           filename='ed.xlsx', report_date='2026-06-30', mapping=payload['mapping'],
                           fingerprint='9ce70be76344f7839cb405c2053cd9e2b5ce750794ff53d84c61793903bd5b1c', readings=[dict(
                               fact_id=i+1, submission_id='synthetic-test', division='ED', source_file='ed.xlsx',
                               source_row=5+i, date='2026-06-30') for i in range(26)] if committed else []))

    def do_POST(self):
        global committed
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert body == payload
        posts.append(self.path)
        if self.path.endswith('/review'):
            self.send({**valid, 'can_confirm': False} if mode == 'invalid' else valid, 503 if mode == 'provider-failure' else 200)
        else:
            assert self.path.endswith('/confirm')
            if mode == 'http409':
                self.send({'detail': 'Synthetic conflict'}, 409)
                return
            committed = mode != 'timeout-uncommitted'
            if mode.startswith('timeout'):
                time.sleep(11)
            self.send(dict(submission_id='synthetic-test', readings_imported=26))


def execute(manifest, base, approval, label):
    result = subprocess.run([CLI, 'rpa', 'run', '--file-path', 'ConfirmSubmission.cs', '--project-dir', str(ROOT),
                             '--profile', 'vantagenet-local-noauth', '--skip-build', '--output', 'json',
                             '--input-arguments', f'manifestPath={manifest}', '--input-arguments', f'baseUrl={base}',
                             '--input-arguments', f'approvalPath={approval}'], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                            env={**os.environ, 'UIPATH_CLI_DISABLE_AUTOINSTALL': 'true', 'UIPATH_CLI_DISABLE_VERSION_SYNC': 'true'})
    (OUT / f'{label}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    return result


def main():
    global mode, committed
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    results = []
    try:
        for index, mode in enumerate(['success', 'missing-authorization', 'missing-approval', 'rejected', 'stale', 'mismatched', 'invalid', 'http409',
                     'provider-failure', 'timeout-committed', 'timeout-uncommitted', 'duplicate']):
            committed = mode == 'duplicate'
            posts.clear()
            folder = OUT / str(index)
            folder.mkdir()
            preview = json.dumps(dict(submission_id='synthetic-test'))
            binding = hashlib.sha256(preview.encode()).hexdigest()
            d = dict(decision='approve', authorize_confirm=mode != 'missing-authorization', reviewer='SYNTHETIC TEST ACTOR',
                     reason='Automated fixture, never a human approval', backend_instance_id='synthetic-test-instance',
                     submission_id='synthetic-test', run_id=mode, preview_sha256=binding,
                     mapping=payload['mapping'], default_direction=None,
                     decided_at=(datetime.now(timezone.utc)-timedelta(days=2 if mode == 'stale' else 0)).isoformat())
            raw = json.dumps(d)
            digest = hashlib.sha256(raw.encode()).hexdigest()
            attempt = folder / 'reviews' / digest
            attempt.mkdir(parents=True)
            def save(path, obj):
                path.write_text(json.dumps(obj))
            (folder / 'preview.json').write_text(preview)
            (attempt / 'decision.json').write_text(raw)
            save(folder / 'manifest.json', dict(submission_id='synthetic-test', run_id=mode, filename='ed.xlsx', state='awaiting_human_review',
                                               division='ED', report_date='2026-06-30', confirmed=False,
                                               sha256='8f35c686bb3f27521637787694d061660f657ac9a2a87ba4aeaedd77d9d3a498'))
            save(folder / 'review-request.json', dict(submission_id='synthetic-test', run_id=mode, base_url=base+'/', preview_sha256=binding))
            save(attempt / 'review-payload.json', payload if mode != 'mismatched' else {**payload, 'default_direction': 'Lower better'})
            save(attempt / 'review-response.json', valid)
            save(attempt / 'result.json', dict(state='mapping_approved_confirm_disabled', submission_id='synthetic-test', decision_sha256=digest, preview_sha256=binding))
            if mode == 'rejected':
                rejected = folder / 'reviews' / 'rejection'
                rejected.mkdir()
                save(rejected / 'decision.json', {'decision': 'reject'})
            result = execute(folder / 'manifest.json', base, attempt / ('missing.json' if mode == 'missing-approval' else 'decision.json'), mode)
            assert (result.returncode == 0) == (mode == 'success'), (mode, result.stdout[-1000:])
            count = sum(p.endswith('/confirm') for p in posts)
            assert count == (1 if mode in ('success','http409','timeout-committed','timeout-uncommitted') else 0), (mode,posts)
            if mode in ('success', 'http409', 'timeout-committed', 'timeout-uncommitted'):
                replay = execute(folder / 'manifest.json', base, attempt / 'decision.json', mode+'-recovery')
                assert (replay.returncode == 0) == (mode in ('success','timeout-committed'))
                assert sum(p.endswith('/confirm') for p in posts) == count
            results.append(dict(case=mode, passed=True, confirm_posts=count))
            print(mode, 'passed', flush=True)
    finally:
        server.shutdown()
        (OUT / 'summary.json').write_text(json.dumps(dict(synthetic_only=True, human_approval=False, tests=results), indent=2))
        print('Evidence:', OUT, flush=True)


if __name__ == '__main__':
    main()

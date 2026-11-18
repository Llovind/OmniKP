"""Loopback transport fixture, NOT AI evidence. No database/provider/network dependencies."""
import hashlib
import json
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT.parents[2] / 'frontend/public/demo/divisions/ed.xlsx'


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        assert self.path == '/api/v1/domains/1/submissions/preview', self.path
        body = self.rfile.read(int(self.headers['Content-Length']))
        message = BytesParser(policy=default).parsebytes(
            b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\n\r\n' + body)
        parts = {p.get_param('name', header='content-disposition'): p for p in message.iter_parts()}
        assert parts['file'].get_payload(decode=True) == FIXTURE.read_bytes()
        for key, value in dict(division='ED', report_date='2026-06-30', sheet_name='Report',
                               header_row='4', header_depth='1', use_ai='true').items():
            assert parts[key].get_payload(decode=True).decode() == value, key
        mode = (ROOT / 'Tests/mode.txt').read_text().strip()
        payload = dict(submission_id='transport-fixture-only', columns=['KPI WISA', 'Realisasi'],
                       column_mapping={'KPI WISA': {'target': 'kpi_name', 'reason': 'fixture'},
                                       'Realisasi': {'target': 'actual_value', 'reason': 'fixture'}},
                       ai_trace={'mode': 'live', 'test_fixture': True},
                       raw_preview=[], issues=[], conflicts=[], can_confirm=False)
        if mode == 'malformed':
            payload.pop('submission_id')
        self.send_response(503 if mode == 'provider-failure' else 200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'detail': 'Synthetic provider failure'} if mode == 'provider-failure' else payload).encode())
        with (ROOT / 'Tests/requests.jsonl').open('a') as f:
            f.write(json.dumps({'mode': mode, 'path': self.path,
                                'sha256': hashlib.sha256(parts['file'].get_payload(decode=True)).hexdigest()}) + '\n')


if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 18761), Handler).serve_forever()

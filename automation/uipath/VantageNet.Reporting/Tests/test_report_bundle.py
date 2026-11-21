"""Synthetic bundle integrations; creates NO decisions and never invokes backend or delivery."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

p = Path(__file__).resolve().parents[1]
root = p.parents[2]
out = p / 'Output' / ('s43-tests-' + uuid.uuid4().hex[:8])
out.mkdir(parents=True)
env = {**os.environ, 'UIPATH_CLI_DISABLE_AUTOINSTALL': 'true', 'UIPATH_CLI_DISABLE_VERSION_SYNC': 'true'}
from cli_support import CLI as cli
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
results = []

def run(label, path, error=None, workflow='AdaptReportBundle.cs', **inputs):
    if workflow == 'AdaptReportBundle.cs':
        inputs = dict(bundlePath=path, **inputs)
    cmd = [cli, 'rpa', 'run', '--file-path', workflow, '--project-dir', str(p), '--profile', 'vantagenet-local-noauth', '--skip-build', '--output', 'json']
    for k, v in inputs.items(): cmd += ['--input-arguments', f'{k}={v}']
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150, env=env)
    text = r.stdout + r.stderr
    (out / (label + '.log')).write_text(text, encoding='utf-8')
    assert (error in text and 'Failure' in text) if error else ('"hasErrors": false' in text and '"errorMessage": null' in text), text
    results.append(label)
    print(label + ': PASS', flush=True)

def write(label, b):
    path = out / (label + '.json')
    path.write_text(json.dumps(b, indent=2), encoding='utf-8')
    return path

b = json.loads((p / 'Data/s43-report-bundle.synthetic.json').read_text())
b['bundle_id'] = out.name
b['snapshot']['run_id'] = out.name + '-v1'
source = write('ready', b)
run('ready', source)
folder = p / 'Output/ReportBundles' / b['snapshot']['run_id']
snapshot = json.loads((folder / 'snapshot.json').read_text())
assert snapshot['bundle_binding']['bundle_sha256'] == sha(source)
hashes = {f.name: sha(f) for f in folder.iterdir()}
run('replay', source)
assert hashes == {f.name: sha(f) for f in folder.iterdir()}
changed = copy.deepcopy(b)
changed['snapshot']['reading']['actual_value'] = 1
run('same-version-change-refused', write('changed', changed), 'Bundle revision changed')
for label, key, value, error in [
    ('version', 'schema_version', 3, 'Unsupported report bundle version'),
    ('backend', 'source_kind', 'backend-read-bundle', 'Report bundle source does not match its version'),
    ('scope', 'scope', {**b['scope'], 'division': 'MBB'}, 'Report scope mismatch')]:
    bad = copy.deepcopy(b); bad[key] = value
    run(label + '-refused', write(label, bad), error)
for i, status in enumerate(['awaiting_feedback', 'provider_unavailable', 'insufficient_evidence'], 2):
    blocked = copy.deepcopy(b); blocked['revision'] = f'v{i}'; blocked['snapshot']['run_id'] = out.name + f'-v{i}'; blocked['evidence_status'] = status
    run(status, write(status, blocked))
    f = p / 'Output/ReportBundles' / blocked['snapshot']['run_id']
    assert not (f / 'snapshot.json').exists()
    state = json.loads((f / 'state.json').read_text())
    assert state['state'] == 'blocked_' + status and state['notification_delivery'] == 'disabled'

# Synthetic v2 contract cases. They exercise admission without claiming a live AI run.
v2 = copy.deepcopy(b)
v2.update(schema_version=2, source_kind='backend-read-bundle', ai_invoked=True, bundle_id=out.name + '-v2-case')
v2['producer'] = dict(disposable=True, domain_id=1, instance_id='test-instance',
                      submission_fingerprint='a'*64, reading_sha256='b'*64)
v2['scope']['fact_id'] = '101'
report = v2['snapshot']
report.update(schema_version=2, origin='backend-confirmed-submission', run_id=v2['bundle_id'] + '-v1')
report['reading'].update(fact_id='101', chart_supported=True)
record = dict(feedback_id='1', fact_id='101', reference='F1', origin='fixture-worksheet-notes')
report['feedback'].update(fact_id='101', count=1, records=[record], origin=record['origin'])
report['narrative'].update(origin='live-provider-rca', ai_invoked=True, cited_feedback_ids=['1'],
                           grounding=dict(citation_verified=True),
                           references=[dict(id='F1', feedback_id='1', origin=record['origin'])])
v2_path = write('v2-contract', v2)
run('wrong-instance-refused', v2_path, 'designated disposable backend', expectedInstanceId='other-instance')
wrong_fact = copy.deepcopy(v2)
wrong_fact['snapshot']['feedback']['records'][0]['fact_id'] = '102'
run('cross-reading-feedback-refused', write('cross-reading', wrong_fact),
    'Feedback record identity or provenance mismatch', expectedInstanceId='test-instance')
run('v2-contract-admitted', v2_path, expectedInstanceId='test-instance')
v2_folder = p / 'Output/ReportBundles' / report['run_id']
staged = json.loads((v2_folder / 'snapshot.json').read_text())
assert staged['origin'] == 'backend-confirmed-submission'
assert staged['bundle_binding']['bundle_sha256'] == sha(v2_path)
run('v2-review-prepare', None, workflow='ReviewNarrative.cs', snapshotPath=v2_folder / 'snapshot.json',
    templatePath=p / 'Data/provisional-report-template.pptx')

# Self-contained SYNTHETIC stale-decision setup; never uses a real approval or old Output.
s = json.loads((p / 'Data/s42-report.synthetic.json').read_text())
s['run_id'] = out.name + '-stale-approval'
test_source = write('review-source', s)
run('stale-review-prepare', None, workflow='ReviewNarrative.cs', snapshotPath=test_source, templatePath=p / 'Data/provisional-report-template.pptx')
review = p / 'Output/NarrativeReview' / s['run_id']
request = json.loads((review / 'request.json').read_text())
from datetime import datetime, timezone
synthetic = {k:request[k] for k in ['run_id','submission_id','snapshot_sha256','narrative_sha256','template_sha256']}
synthetic.update(reviewer='synthetic-regression-actor-not-human', reason='Synthetic stale-decision regression only.', decision='approve', reviewed_narrative='Synthetic test narrative; not live RCA or a genuine human decision.', decided_at=datetime.now(timezone.utc).isoformat())
approval = write('synthetic-stale-decision', synthetic)
approval_before = sha(approval)
s['reading']['actual_value'] = 1
changed_source = write('changed-source', s)
test_folder = out / 'changed-data-request'; test_folder.mkdir()
(test_folder / 'snapshot.json').write_bytes(changed_source.read_bytes())
request['snapshot_path'] = str(changed_source); request['snapshot_sha256'] = sha(changed_source)
request_path = test_folder / 'request.json'; request_path.write_text(json.dumps(request))
run('old-approval-changed-data-refused', None, 'Stale or mismatched narrative decision: snapshot_sha256', workflow='GenerateNarrativePptx.cs', requestPath=request_path, decisionPath=approval)
assert sha(approval) == approval_before and not list(test_folder.glob('*.pptx')) and not (test_folder / 'generation-intent.json').exists()
assert not (folder / 'decisions').exists() and not list(folder.glob('*.pptx'))
summary = dict(passed=results, synthetic_decision_created=True, human_approvals_used=False, synthetic_decision_unchanged=True, backend_called=False, notification_delivered=False, report_generated=False, test_dir=str(out))
(out / 'results.json').write_text(json.dumps(summary, indent=2))
(p / 'Output/s43-evidence').mkdir(exist_ok=True)
(p / 'Output/s43-evidence/results.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary), flush=True)

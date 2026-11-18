"""Actual UiPath regression with EXPLICIT SYNTHETIC decisions; never human acceptance evidence."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
from pptx import Presentation

p = Path(__file__).resolve().parents[1]
out = p / 'Output' / ('s42-tests-' + uuid.uuid4().hex[:8])
out.mkdir(parents=True)
from cli_support import CLI as cli
env = {**os.environ, 'UIPATH_CLI_DISABLE_AUTOINSTALL': 'true', 'UIPATH_CLI_DISABLE_VERSION_SYNC': 'true'}
template = p / 'Data/provisional-report-template.pptx'
read = lambda path: json.loads(path.read_bytes().decode('utf-8-sig'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
results = []

def run(workflow, label, error=None, **inputs):
    args = [cli, 'rpa', 'run', '--project-dir', str(p), '--file-path', workflow,
            '--skip-build', '--profile', 'vantagenet-local-noauth', '--output', 'json']
    for key, value in inputs.items():
        args += ['--input-arguments', f'{key}={value}']
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=150)
    text = r.stdout + r.stderr
    (out / (label + '.log')).write_text(text, encoding='utf-8')
    if error:
        assert error in text and 'Failure' in text, text
    else:
        assert '"hasErrors": false' in text and '"errorMessage": null' in text, text
    print(label + ': PASS', flush=True)

def case(name):
    s = read(p / 'Data/s42-report.synthetic.json')
    s['run_id'] = 'synthetic-regression-' + out.name + '-' + name
    source = out / (name + '.snapshot.json')
    source.write_text(json.dumps(s), encoding='utf-8')
    run('ReviewNarrative.cs', name + '-prepare', snapshotPath=source, templatePath=template)
    folder = p / 'Output/NarrativeReview' / s['run_id']
    return source, folder, read(folder / 'request.json')

def decision(name, r, action='approve', edited='SYNTHETIC AUTOMATED TEST: edited narrative preserved exactly.\nNo genuine human approval or live RCA.'):
    d = {k: r[k] for k in ['run_id', 'submission_id', 'snapshot_sha256', 'narrative_sha256', 'template_sha256']}
    d.update(reviewer='synthetic-regression-actor-not-human', reason='Automated regression only; not attended acceptance.', decision=action, reviewed_narrative=edited, decided_at=datetime.now(timezone.utc).isoformat())
    path = out / (name + '.synthetic-decision.json')
    path.write_text(json.dumps(d, indent=2), encoding='utf-8')
    return path

source, folder, r = case('missing')
run('GenerateNarrativePptx.cs', 'missing-approval-blocked', 'Missing narrative approval', requestPath=folder / 'request.json', decisionPath=out / 'does-not-exist.json')
assert not list(folder.glob('*.pptx'))
for action in ['reject', 'request_revision']:
    source, folder, r = case(action)
    d = decision(action, r, action)
    original_hash = sha(d)
    run('ReviewNarrative.cs', action + '-resume', snapshotPath=source, templatePath=template, decisionPath=d)
    run('GenerateNarrativePptx.cs', action + '-blocked', 'Narrative approval required', requestPath=folder / 'request.json', decisionPath=d)
    assert sha(d) == original_hash and not list(folder.glob('*.pptx'))
    override = decision(action + '-override', r, 'approve')
    run('ReviewNarrative.cs', action + '-override-blocked', 'Narrative rejected or revision requested', snapshotPath=source, templatePath=template, decisionPath=override)
    results.append(action + '-blocks-pptx')

source, folder, r = case('changed')
d = decision('changed', r)
run('ReviewNarrative.cs', 'changed-resume', snapshotPath=source, templatePath=template, decisionPath=d)
s = read(source)
s['reading']['actual_value'] = 1
source.write_text(json.dumps(s), encoding='utf-8')
run('GenerateNarrativePptx.cs', 'changed-snapshot-blocked', 'Snapshot changed', requestPath=folder / 'request.json', decisionPath=d)
assert not list(folder.glob('*.pptx'))

source, folder, r = case('expired')
d = decision('expired', r)
s = read(d)
s['decided_at'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
d.write_text(json.dumps(s))
run('ReviewNarrative.cs', 'expired-blocked', 'Narrative decision is expired', snapshotPath=source, templatePath=template, decisionPath=d)

source, folder, r = case('mismatch')
d = decision('mismatch', r)
s = read(d)
s['narrative_sha256'] = '0' * 64
d.write_text(json.dumps(s))
run('ReviewNarrative.cs', 'narrative-hash-mismatch-blocked', 'Stale or mismatched narrative decision', snapshotPath=source, templatePath=template, decisionPath=d)

source, folder, r = case('overlong')
d = decision('overlong', r, edited='Synthetic text ' * 70)
run('ReviewNarrative.cs', 'overlong-narrative-blocked', 'exceeds provisional template capacity', snapshotPath=source, templatePath=template, decisionPath=d)

source, folder, r = case('edited')
d = decision('edited', r)
original_hash = sha(d)
run('ReviewNarrative.cs', 'edited-resume', snapshotPath=source, templatePath=template, decisionPath=d)
run('GenerateNarrativePptx.cs', 'edited-generate', requestPath=folder / 'request.json', decisionPath=d)
pptx = folder / (r['run_id'] + '.pptx')
ppt = Presentation(pptx)
assert len(ppt.slides) == 3
texts = {shape.name: shape.text for slide in ppt.slides for shape in slide.shapes if shape.has_text_frame}
assert texts['Narrative'] == read(d)['reviewed_narrative']
assert read(source)['narrative']['draft'] != texts['Narrative']
reading = read(source)['reading']
for key in ['kpi_name', 'fact_id', 'location_name', 'status']:
    assert str(reading[key]) in texts['KPI']
assert str(reading['actual_value']) in texts['Comparison'] and str(reading['target_value']) in texts['Comparison']
assert reading['source_file'] in texts['Source'] and str(reading['source_row']) in texts['Source']
assert r['snapshot_sha256'] in texts['Source'] and original_hash in texts['Source']
assert read(source)['report_date'] in texts['Scope'] and read(source)['division'] in texts['Scope']
assert 'F1' in texts['References'] and 'synthetic-fixture-not-human-feedback' in texts['References']
before = {f.name: sha(f) for f in folder.glob('*.pptx')}
run('GenerateNarrativePptx.cs', 'edited-replay', requestPath=folder / 'request.json', decisionPath=d)
assert {f.name: sha(f) for f in folder.glob('*.pptx')} == before
assert sha(d) == original_hash
pdf = out / 'synthetic-render-proof.pdf'
run('RenderReportProof.cs', 'powerpoint-open-render', pptxPath=pptx, pdfPath=pdf)
assert pdf.exists() and pdf.read_bytes().startswith(b'%PDF')
import pypdfium2 as pdfium
document = pdfium.PdfDocument(str(pdf))
assert len(document) == 3
for i, page in enumerate(document):
    assert page.get_textpage().get_text_range().strip()
    page.render(scale=1).to_pil().save(out / f'render-{i+1}.png')
summary = dict(synthetic_decisions_only=True, genuine_human_acceptance=False,
               missing_approval_blocked=True, reject_blocked=True, revision_blocked=True,
               changed_snapshot_blocked=True, expired_approval_blocked=True,
               narrative_hash_mismatch_blocked=True, overlong_text_blocked=True,
               exact_edited_narrative_preserved=True, source_content_verified=True,
               replay_no_duplicate=True, powerpoint_open_and_pdf_render=True,
               pptx=str(pptx), pdf=str(pdf), evidence=str(out))
(out / 'results.json').write_text(json.dumps(summary, indent=2))
(p / 'Output/s42-evidence').mkdir(exist_ok=True)
(p / 'Output/s42-evidence/latest-test-run.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary), flush=True)

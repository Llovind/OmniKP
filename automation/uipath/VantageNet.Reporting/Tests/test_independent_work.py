"""Actual UiPath offline executions. No approval generation, delivery, API or AI calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parents[1]
out = project / 'Output/independent-tests'
out.mkdir(parents=True, exist_ok=True)
from cli_support import CLI as cli
env = {**os.environ, 'UIPATH_CLI_DISABLE_AUTOINSTALL': 'true', 'UIPATH_CLI_DISABLE_VERSION_SYNC': 'true'}

def run(config, label, error=None):
    command = [cli, 'rpa', 'run', '--file-path', 'PrepareReportWork.cs', '--project-dir', str(project), '--profile', 'vantagenet-local-noauth', '--skip-build', '--input-arguments', f'configPath={config}', '--output', 'json']
    r = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=150)
    text = r.stdout + r.stderr
    (out / (label + '.log')).write_text(text, encoding='utf-8')
    if error:
        assert error in text and ('"hasErrors": true' in text or '\\"hasErrors\\":true' in text or 'Failure' in text), text
    else:
        assert '"hasErrors": false' in text and '"errorMessage": null' in text, text

config = project / 'Data/independent-work-config.json'
run(config, 'prepare')
folder = project / 'Output/IndependentReportWork/offline-ed-report-001'
hashes = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}
before = hashes()
state = json.loads((folder / 'state.json').read_text())
assert state['notification_state'] == 'draft_only_not_delivered'
assert state['state'] == 'awaiting_human_narrative_review'
assert 'X-Unsent: 1' in (folder / 'notification.eml').read_text()
assert 'SYNTHETIC SCRIPT' in (folder / 'narrative-review.html').read_text()
job = json.loads((folder / 'pptx-job.json').read_text())
assert job['approved_narrative'] is None and job['template_path'] is None
assert not list(folder.glob('*.pptx'))
run(config, 'replay')
assert hashes() == before
data = json.loads((project / 'Data/independent-work.synthetic.json').read_text())
data['narrative']['draft'] = 'Changed synthetic draft requiring a new review.'
(out / 'changed.json').write_text(json.dumps(data))
cfg = dict(input_path='changed.json', delivery_mode='draft_only', test_recipient='ed@example.invalid')
(out / 'changed-config.json').write_text(json.dumps(cfg))
run(out / 'changed-config.json', 'changed-input-refused', 'Run inputs changed')
cfg['delivery_mode'] = 'send'
(out / 'send-config.json').write_text(json.dumps(cfg))
run(out / 'send-config.json', 'delivery-refused', 'Only explicit synthetic local inputs')
assert hashes() == before
(out / 'results.json').write_text(json.dumps(dict(prepare=True, replay_unchanged=True, changed_input_refused=True, delivery_mode_refused=True, approval_created=False, notification_delivered=False, pptx_generated=False), indent=2))
print('PASS: actual UiPath preparation, byte-stable replay, changed-input refusal, delivery-mode refusal. No human approval, delivery or PPTX generated.')

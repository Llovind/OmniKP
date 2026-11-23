import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { createHash, webcrypto } from 'node:crypto';

const project = new URL('../', import.meta.url);
const read = name => fs.readFileSync(new URL(name, project), 'utf8');
const label = 'SYNTHETIC ACCEPTANCE SCENARIO';
const explanation = label + ' — This is hypothetical test input, not a verified operational observation.\n\n' +
  'The Demo South deployment count is below its reporting target. For this test scenario, assume that several planned deployment activities are awaiting site-access coordination.';
const action = 'Review the pending deployment list, identify activities awaiting access approval, and coordinate revised execution schedules with the responsible teams.';
const manifest = JSON.parse(read('project.json'));
const paths = manifest.entryPoints.map(entry => entry.filePath);
assert.equal(paths.filter(path => path === 'SubmitOperatorFeedback.cs').length, 1);
for (const path of ['Main.xaml', 'AdmitBackendReportBundleV2.cs', 'ReviewBackendNarrativeV2.cs',
  'GenerateBackendNarrativePptxV2.cs', 'RenderReportProof.cs']) assert.ok(paths.includes(path), path);

const reading = {
  kpi_name:'DEP-WHF-Deployment Alpro', location_name:'Demo South', date:'2026-06-30', division:'ED',
  actual_value:546, target_value:600, unit:'Port', source_file:'ed.xlsx', source_row:16, fact_id:'12', status:'Below target'
};
const binding = {instance_id:'vantagenet-acceptance-20261121-e63c', submission_id:'aff04920-b5ee-4ddd-9786-9c94a7549d35', fact_id:12};
const request = {binding, reading, scenario_label:label, request_id:'offline-request',
  payload:{fact_id:12, explanation, corrective_action:action}};
const hash = createHash('sha256').update(JSON.stringify(request)).digest('hex');

function runForm(file, marker, data) {
  const html = read(file);
  assert.ok(html.includes(marker));
  const script = html.replace(marker, JSON.stringify(data)).match(/<script>([\s\S]+)<\/script>/)[1];
  const elements = new Map(), downloads = [];
  let blobData;
  const create = () => ({
    textContent:'', value:'', checked:false, disabled:true, hidden:true, children:[],
    append(...nodes) { this.children.push(...nodes); },
    click() { downloads.push({filename:this.download, value:blobData}); }
  });
  const get = id => {
    if (!elements.has(id)) elements.set(id, create());
    return elements.get(id);
  };
  class TestBlob { constructor([payload]) { blobData = JSON.parse(payload); } }
  vm.runInNewContext(script, {
    document:{getElementById:get, createElement:create}, Blob:TestBlob, crypto:webcrypto, TextEncoder,
    URL:{createObjectURL:()=> 'blob:offline', revokeObjectURL(){}}, setTimeout:fn=>fn(),
    fetch:()=> { throw Error('Form tried to send a live request'); }
  });
  return {html, get, downloads};
}

const review = runForm('Data/operator-feedback-review.html', '/*OPERATOR_FEEDBACK_DATA*/null',
  {request, request_sha256:hash});
assert.match(review.html, /<strong>SYNTHETIC ACCEPTANCE SCENARIO<\/strong>/);
assert.equal(review.get('explanation').textContent, explanation);
assert.equal(review.get('action').textContent, action);
assert.ok(review.get('reading').children.some(item => item.textContent === '54 Port'));
review.get('save').onclick();
assert.equal(review.downloads.length, 0);
review.get('ack').checked = true;
review.get('ack').onchange();
assert.equal(review.get('save').disabled, false);
review.get('save').onclick();
assert.equal(review.downloads.length, 1);
assert.deepEqual(Object.keys(review.downloads[0].value).sort(),
  ['acknowledged', 'decided_at', 'decision', 'request_id', 'request_sha256', 'scenario_label']);
assert.equal(review.downloads[0].value.scenario_label, label);
assert.equal(review.downloads[0].value.request_sha256, hash);
assert.equal(review.downloads[0].value.decision, 'submit_synthetic_feedback');
assert.match(review.get('message').textContent, /No feedback was sent/);

const narrativeData = {
  request:{binding:{run_id:'offline-v1', fact_id:'12', scenario_label:label}, request_id:'offline-narrative'},
  request_sha256:hash,
  snapshot:{reading, run_id:'offline-v1', submission_id:binding.submission_id, division:'ED', report_date:reading.date,
    feedback:{records:[{reference:'F6', origin:'operator-api', explanation, corrective_action:action}]},
    narrative:{draft:'Offline fixture draft [F6].', llm_model:'mock', provider_status:'response_accepted', references:[{id:'F6'}]}}
};
const narrative = runForm('Data/backend-narrative-review-v2.html', '/*BACKEND_V2_REVIEW_DATA*/null', narrativeData);
assert.match(narrative.get('feedback').children[0].textContent, /Operator API feedback[\s\S]*SYNTHETIC ACCEPTANCE SCENARIO/);
assert.equal(narrative.get('narrative').value, narrative.get('original').textContent);
narrative.get('reviewer').value = 'Offline browser fixture';
narrative.get('reason').value = 'Offline fixture for label retention.';
narrative.get('decision').value = 'request_revision';
await narrative.get('save').onclick();
assert.equal(narrative.downloads[0].value.binding.scenario_label, label);

delete narrativeData.request.binding.scenario_label;
const routine = runForm('Data/backend-narrative-review-v2.html', '/*BACKEND_V2_REVIEW_DATA*/null', narrativeData);
assert.ok(!routine.html.includes('hypothetical acceptance feedback'));
assert.equal(routine.get('original').textContent, 'Offline fixture draft [F6].');
console.log('PASS attended synthetic form and downstream v2 form regressions');

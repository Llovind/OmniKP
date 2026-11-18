// DOM contract test for the generated local form. Not a real browser/human walkthrough.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html = fs.readFileSync(process.argv[2], 'utf8');
class Element {
  constructor(){ this.children=[]; this.value=''; this.textContent=''; }
  append(e){this.children.push(e)}
  setAttribute(k,v){this[k]=v}
  click(){this.clicked=true}
}
const ids = new Map();
for(const id of ['context','rows','validation','reviewer','reason','decision','direction','save','message','instance','confirm','proposalSource','approvalContext']) ids.set('#'+id,new Element());
const body=new Element();let blob;
const document={body,querySelector:id=>ids.get(id),createElement:()=>new Element()};
vm.runInNewContext(html.match(/<script>([\s\S]*)<\/script>/)[1], {document,Blob,URL:{createObjectURL:b=>(blob=b,'blob:test'),revokeObjectURL:()=>{}},setTimeout:()=>{}});
assert.equal(ids.get('#rows').children.length,3);
assert.equal(ids.get('#rows').children[0].children[1].textContent,'"<script>bad()</script>"');
ids.get('#save').onclick();assert.match(ids.get('#message').textContent,/explicit decision/);assert.equal(blob,undefined);
ids.get('#rows').children[1].children[3].children[0].value='actual_value';
ids.get('#reviewer').value='Test reviewer';ids.get('#reason').value='Value is a measurement';ids.get('#decision').value='correct';
ids.get('#save').onclick();
const decision=JSON.parse(await blob.text());assert.equal(decision.mapping.Value,'actual_value');assert.equal(decision.decision,'correct');assert.ok(decision.submission_id);assert.ok(decision.preview_sha256);
assert.equal(decision.authorize_confirm,false);
ids.get('#confirm').checked=true;ids.get('#decision').value='approve';ids.get('#save').onclick();
assert.match(ids.get('#message').textContent,/instance ID/);
ids.get('#instance').value='synthetic-form-contract-instance';ids.get('#save').onclick();
assert.equal(JSON.parse(await blob.text()).authorize_confirm,true);
console.log('Form DOM contract passed: actual text, required decision, corrected mapping download.');

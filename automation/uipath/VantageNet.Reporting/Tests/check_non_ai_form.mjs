// Read-only renderer check of the actual generated ED form. No human actions or decisions simulated.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(process.argv[2],'utf8');
class Element{constructor(){this.children=[];this.value='';this.checked=false;this.textContent='';}append(e){this.children.push(e)}setAttribute(k,v){this[k]=v}}
const ids=new Map();
for(const id of ['context','rows','validation','reviewer','reason','decision','direction','save','message','instance','confirm','proposalSource','approvalContext'])ids.set('#'+id,new Element());
const document={body:new Element(),querySelector:id=>ids.get(id),createElement:()=>new Element()};
vm.runInNewContext(html.match(/<script>([\s\S]*)<\/script>/)[1],{document,Blob,URL:{},setTimeout});
assert.match(ids.get('#proposalSource').textContent,/NON-AI TEST PROPOSAL/);
assert.match(ids.get('#context').textContent,/ed.xlsx \| ED \| 2026-06-30/);
assert.equal(ids.get('#reviewer').value,'');assert.equal(ids.get('#decision').value,'');assert.equal(ids.get('#confirm').checked,false);
const rows=ids.get('#rows').children;
assert.equal(rows.length,7);
const actual=rows.find(r=>r.children[0].textContent==='Realisasi');
assert.ok(actual);assert.equal(actual.children[3].children[0].value,process.argv[3]||'ignore');assert.match(actual.children[1].textContent,/97.8/);
console.log('Actual ED form renderer: explicit NON-AI label, 7 source columns, real synthetic samples, no preselected decision/authorization. No attended action performed.');

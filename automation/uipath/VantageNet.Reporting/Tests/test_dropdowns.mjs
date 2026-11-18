// Renderer regression test only. Never invokes Save, creates a decision, or contacts backend.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(process.argv[2],'utf8');
class Element {
 constructor(tag=''){this.tagName=tag.toUpperCase();this.children=[];this.value='';this.checked=false;this.textContent='';}
 append(e){this.children.push(e)}
 setAttribute(k,v){this[k]=v}
}
const ids=new Map();
for(const id of ['context','rows','validation','reviewer','reason','decision','direction','save','message','instance','confirm','proposalSource','approvalContext'])ids.set('#'+id,new Element());
const document={body:new Element(),querySelector:id=>ids.get(id),createElement:tag=>new Element(tag)};
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
const data=vm.runInNewContext(script+';data',{document,Blob,URL:{},setTimeout});
assert.ok(!html.includes('<datalist')&&!html.includes("setAttribute('list'"));
for(const row of ids.get('#rows').children){
 const select=row.children[3].children[0];assert.equal(select.tagName,'SELECT');
 for(const target of ['ignore','kpi_name','unit','higher_is_better','target_value','location_name','actual_value','notes','date','kpi_archetype'])assert.ok(select.children.some(o=>o.value===target),target);
 const initial=select.value;assert.equal(initial,data.validated_payload?.mapping[row.children[0].textContent]??row.children[2].textContent.split('\n')[0]);assert.ok(select.children.some(o=>o.value===initial));
 const options=select.children.map(o=>o.value);select.value='actual_value';assert.deepEqual(select.children.map(o=>o.value),options);select.value=initial;
}
const actual=ids.get('#rows').children.find(row=>row.children[0].textContent==='Realisasi');
assert.equal(actual.children[3].children[0].value,process.argv[3]||'ignore');
assert.ok(!/<\/option\s+value=/.test(html),'Malformed closing option tag');
const decision=html.match(/<select id="decision"[^>]*>([\s\S]*?)<\/select>/)[1];
assert.deepEqual([...decision.matchAll(/<option value="([^"]*)"/g)].map(m=>m[1]),['','correct','approve','reject']);
const direction=html.match(/<select id="direction"[^>]*>([\s\S]*?)<\/select>/)[1];
assert.equal((direction.match(/<option[ >]/g)||[]).length,3);
assert.equal(ids.get('#decision').value,'');assert.equal(ids.get('#reviewer').value,'');assert.equal(ids.get('#confirm').checked,false);
console.log('Dropdown regressions passed: native selects, complete unfiltered targets, preserved defaults, three distinct decisions; Save never invoked.');

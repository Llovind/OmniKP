import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import { createHash, webcrypto } from 'node:crypto';

const html=fs.readFileSync(process.argv[2],'utf8');
const script=html.match(/<script>([\s\S]+)<\/script>/)[1];
const elements=new Map();
const newElement=()=>({textContent:'',value:'',children:[],append(...items){this.children.push(...items);},click(){downloads++;}});
const get=id=>{if(!elements.has(id)) elements.set(id,newElement());return elements.get(id);};
let downloads=0, decision;
const document={getElementById:get,createElement:newElement};
class CaptureBlob {constructor([payload]){decision=JSON.parse(payload);}}
vm.runInNewContext(script,{document,crypto:webcrypto,TextEncoder,Blob:CaptureBlob,
  URL:{createObjectURL:()=> 'blob:offline-test',revokeObjectURL(){}},setTimeout:fn=>fn()});
assert.equal(get('decision').value,'');
assert.equal(get('reviewer').value,'');
assert.equal(get('original').textContent,get('narrative').value);
assert.match(get('provider').textContent,/response_accepted/);
assert.match(get('feedback').children.map(item=>item.textContent).join('\n'),/Worksheet-derived note[\s\S]*Operator API feedback/);
assert.match(get('citations').textContent,/F2, F11/);
assert.ok(get('reading').children.some(item=>String(item.textContent)==='90.25 %'));
await get('save').onclick();
assert.equal(downloads,0);
get('reviewer').value='Offline browser fixture';
get('decision').value='approve';
get('reason').value='Explicit scripted assertion for this regression only.';
get('narrative').value='Edited narrative in browser fixture.';
await get('save').onclick();
assert.equal(downloads,1);
assert.equal(decision.reviewed_narrative,get('narrative').value);
assert.equal(decision.reviewed_narrative_sha256,createHash('sha256').update(decision.reviewed_narrative).digest('hex'));
assert.match(decision.request_sha256,/^[a-f0-9]{64}$/);
assert.equal(decision.binding.fact_id,'41');

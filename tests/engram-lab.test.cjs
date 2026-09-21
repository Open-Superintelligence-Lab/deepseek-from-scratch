const assert=require('node:assert/strict');
const E=require('../engram-lab-core.js');
const tokens=E.tokenize('I love New York City');
assert.deepEqual(E.groups(tokens,3)[0].words,['New','York']);
assert.deepEqual(E.groups(tokens,0)[2].words,['PAD','PAD','PAD','I']);
const changedFuture=E.tokenize('I love New York tomorrow');
assert.deepEqual(E.groups(tokens,3),E.groups(changedFuture,3));
assert.equal(E.hash([72,18],0,101),28);
assert.equal(E.hash([1,98],0,101),28);
assert.equal(E.hash([18,72],0,101),24);
const a=E.lookup([72,18],8,101),b=E.lookup([1,98],8,101);
assert.deepEqual(a[0].vector,b[0].vector);
assert.notDeepEqual(a.map(x=>x.row),b.map(x=>x.row));
assert.deepEqual(a,E.lookup([72,18],8,101));
const m=E.retrieve(E.groups(tokens,3),8,101),snapshot=JSON.stringify(m);
assert.equal(m.groups.flatMap(g=>g.lookups).length,24);
const aligned=E.contextGate(m.key,m.value,0),opposite=E.contextGate(m.key,m.value,180),orthogonal=E.contextGate(m.key,m.value,90);
assert.ok(Math.abs(orthogonal.gate-.5)<1e-10);
assert.ok(aligned.gate>.95&&opposite.gate<.05);
assert.equal(JSON.stringify(m),snapshot);
aligned.added.forEach((v,j)=>assert.ok(Math.abs(v-aligned.gate*m.value[j])<1e-12));
assert.ok(Math.hypot(...aligned.hidden)-1<1e-10);
for(const rows of [3,17,101]){
 const result=E.collisionExperiment(rows);
 assert.equal(result.total,256);
 assert.equal(result.one.distinct,rows);
 assert.ok(result.eight.distinct>=result.one.distinct);
 assert.equal(result.addresses[0][0],result.addresses[1][0]);
 if(rows===3){assert.equal(result.eight.distinct,9);assert.deepEqual(result.addresses[0],result.addresses[1]);}
 else {assert.equal(result.eight.distinct,256);assert.equal(result.eight.sharedGroups,0);}
}
assert.equal(E.tokenize(' ').length,0);
assert.equal(E.tokenize('x '.repeat(40)).length,32);
console.log('PASS: causal groups, padding, deterministic table retrieval, collisions, computed gates and enumeration.');

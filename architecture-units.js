(()=>{
 const project=h=>[h[0]+2*h[1],-h[0]+h[1]];
 const gather=(scores,values)=>scores.map((s,i)=>i).sort((a,b)=>scores[b]-scores[a]||a-b).slice(0,2).map(i=>values[i]);
 const mix=(a,b,wa,wb)=>a.map((x,i)=>wa*x+wb*b[i]);
 const equal=(a,b)=>a.length===b.length&&a.every((v,i)=>Math.abs(v-b[i])<1e-9);
 const config={projection:{answer:()=>project([3,3]),explain:'K = 3×1 + 3×2 = 9. V = 3×(−1) + 3×1 = 0. The weights stayed fixed; the input and cache entry changed.',tests:()=>[equal(project([2,3]),[8,1]),equal(project([3,3]),[9,0])]},gather:{answer:()=>gather([.95,.9,.1,.8],[10,20,30,40]),explain:'Scores 0.95 and 0.9 win at positions 0 and 1. Values[0] = 10 and values[1] = 20. Return the retrieved values, not the scores or the addresses.',tests:()=>[equal(gather([.2,.9,.1,.8],[10,20,30,40]),[20,40]),equal(gather([.95,.9,.1,.8],[10,20,30,40]),[10,20])]},mix:{answer:()=>mix([2,0],[0,4],.5,.5),explain:'First coordinate: 0.5×2 + 0.5×0 = 1. Second coordinate: 0.5×0 + 0.5×4 = 2. The result is [1, 2].',tests:()=>[equal(mix([2,0],[0,4],.25,.75),[.5,3]),equal(mix([2,0],[0,4],.5,.5),[1,2])]}};
 document.querySelectorAll('[data-unit]').forEach(root=>{
  const c=config[root.dataset.unit],fields=[...root.querySelectorAll('input')],feedback=root.querySelector('[data-unit-feedback]');
  root.querySelector('[data-unit-check]').addEventListener('click',()=>{const vals=fields.map(f=>f.value.trim());if(vals.some(v=>v==='')||fields.some(f=>!f.validity.valid)||vals.some(v=>!Number.isFinite(Number(v)))){feedback.textContent='Enter a valid number in each box before checking.';feedback.className='unit-feedback';return}const ok=equal(vals.map(Number),c.answer());feedback.textContent=ok?'Correct. '+c.explain:'Not quite. '+(root.dataset.unit==='gather'?'Find the winning positions, then look up the values at those positions.':'Calculate the two coordinates separately. Check the multiplication and signs.');feedback.className='unit-feedback '+(ok?'unit-pass':'unit-retry')});
  root.querySelector('[data-unit-reveal]').addEventListener('click',()=>{feedback.textContent=c.explain;feedback.className='unit-feedback'});
  fields.forEach(f=>f.addEventListener('input',()=>{feedback.className='unit-feedback';feedback.textContent='Your answer changed. Check both numbers again.'}));
  root.querySelector('[data-unit-run]').addEventListener('click',()=>{const results=c.tests();root.querySelector('[data-unit-test-result]').textContent=results.every(Boolean)?'PASS · 2/2 browser checks. Both the worked input and the changed input match their expected outputs.':'FAIL · '+results.filter(Boolean).length+'/2 checks passed.'});
 });
})();

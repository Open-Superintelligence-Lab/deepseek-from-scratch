(()=>{
 const select=document.getElementById('task-candidate');if(!select)return;
 const candidates={shortcut:{code:'return 0;',fn:()=>0},boundary:{code:'return subtotal > 50 ? 0 : 5;',fn:x=>x>50?0:5},correct:{code:'return subtotal >= 50 ? 0 : 5;',fn:x=>x>=50?0:5}};
 const cases=[{x:60,want:0,kind:'Requested change'},{x:50,want:0,kind:'Exact boundary'},{x:20,want:5,kind:'Preserve existing behavior'}];let suite='weak';
 function draw(){
  const c=candidates[select.value],tests=suite==='weak'?cases.slice(0,1):cases;
  document.getElementById('task-candidate-code').textContent=c.code;let passed=0;
  document.getElementById('task-test-results').replaceChildren(...tests.map(t=>{
   const actual=c.fn(t.x),ok=actual===t.want;if(ok)passed++;
   const row=document.createElement('div');row.className='taskbuild-test '+(ok?'passed':'failed');
   const label=document.createElement('strong');label.textContent=`${ok?'✓ PASS':'✕ FAIL'} · $${t.x} order`;
   const result=document.createElement('span');result.textContent=`Shipping: $${actual}. Expected: $${t.want}. ${t.kind}.`;row.append(label,result);return row;
  }));
  document.querySelectorAll('[data-task-suite]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.taskSuite===suite)));
  document.getElementById('task-verifier-feedback').textContent=`${passed}/${tests.length} checks pass. `+(suite==='weak'?'All three implementations pass this one check. It cannot distinguish the correct behavior from either bug. Try adding boundary and regression checks.':passed===tests.length?'This implementation satisfies all three checks for the stated toy task. A passing result is bounded by what those checks cover.':'The stronger checks expose a mismatch with the request. Inspect the failing case, then change the implementation.');
 }
 select.addEventListener('change',draw);document.querySelectorAll('[data-task-suite]').forEach(b=>b.addEventListener('click',()=>{suite=b.dataset.taskSuite;draw()}));draw();
})();

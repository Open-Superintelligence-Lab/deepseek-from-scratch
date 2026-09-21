(()=>{
 const run=document.getElementById('offset-run');if(!run)return;
 run.addEventListener('click',()=>{
  const prediction=document.getElementById('offset-prediction').value;
  const result=document.getElementById('offset-result');
  if(!prediction){result.textContent='Choose a prediction first. An incorrect guess is useful too.';return;}
  const corrected=document.getElementById('offset-mode').value==='correct';
  const local=[1,1],offsets=[0,3],table=[[0,0],[.2,-.5],[0,0],[0,0],[.6,.1],[0,0],[0,0]];
  const rows=local.map((v,i)=>v+(corrected?offsets[i]:0));
  const vectors=rows.map(i=>table[i]);
  const verdict=prediction==='same'?'Your prediction about removing offsets was correct.':'Removing offsets makes both heads retrieve A1. The lookup still runs.';
  result.textContent=`${verdict}\n\nThis run: offsets ${corrected?'ON':'OFF'}\nGlobal rows: ${JSON.stringify(rows)}\nHead A: ${JSON.stringify(vectors[0])}\nHead B: ${JSON.stringify(vectors[1])}\n\n${corrected?'Head B now reads its own region.':'Head B incorrectly reads head A’s region. Restore the offsets and run again.'}`;
  if(corrected)document.dispatchEvent(new CustomEvent('course-task-complete',{detail:'packed-offsets'}));
 });
})();

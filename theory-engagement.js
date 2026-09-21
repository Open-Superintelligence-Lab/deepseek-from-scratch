// Small illustrative checks. These do not run a model or change course completion.
(()=>{
 const quizzes={
  selection:{correct:1,yes:'Exactly. All 8 entries remain stored. This query reads 3 of them. Selection changes the read set; it does not delete the other 5.',no:'The cache still contains all 8 entries. Top-K chooses which entries this query reads. It does not evict the others. Try the storage answer again.'},
  evidence:{correct:1,yes:'Yes. The reported score increased by 5.8 points in this evaluation. The table compares whole models, so it cannot assign that gain to CSA2 alone. MGSM also fell in the displayed rows.',no:'The scores compare finished models with several differences. They support the observed MMLU-Pro improvement, not a cause for it—and the MGSM row shows that not every score improved. Try again.'}
 };
 document.querySelectorAll('[data-theory-quiz]').forEach(root=>{
  const q=quizzes[root.dataset.theoryQuiz];if(!q)return;
  root.querySelectorAll('[data-quiz-choice]').forEach(button=>button.addEventListener('click',()=>{
   root.querySelectorAll('[data-quiz-choice]').forEach(b=>{b.setAttribute('aria-pressed',String(b===button));b.classList.remove('is-correct','is-retry')});
   const correct=Number(button.dataset.quizChoice)===q.correct;
   button.classList.add(correct?'is-correct':'is-retry');
   root.querySelector('[data-quiz-feedback]').textContent=q[correct?'yes':'no'];
  }));
 });
 const root=document.getElementById('expert-load-demo');if(!root)return;
 const modes={crowded:[9,1,1,1],spread:[3,3,3,3]};
 function draw(mode){
  const counts=modes[mode];
  root.querySelectorAll('[data-load-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.loadMode===mode)));
  root.querySelector('[data-load-bars]').replaceChildren(...counts.map((n,i)=>{
   const row=document.createElement('div');row.className='expert-load-row';
   const label=document.createElement('span');label.textContent=`Expert ${'ABCD'[i]}`;
   const track=document.createElement('div');track.className='expert-load-track';
   const bar=document.createElement('i');bar.style.width=`${n/12*100}%`;track.append(bar);
   const amount=document.createElement('strong');amount.textContent=`${n} token${n===1?'':'s'}`;
   row.append(label,track,amount);return row;
  }));
  root.querySelector('[data-load-explanation]').textContent=mode==='crowded'?'Expert A receives 9 of the 12 tokens. If four identical workers process one token at a time in parallel, the busiest worker needs 9 time units. Others finish early and wait.':'Each expert receives 3 tokens. Under the same simplified worker assumption, the busiest worker needs 3 time units. Total work is still 12 tokens; only its distribution changed.';
 }
 root.querySelectorAll('[data-load-mode]').forEach(b=>b.addEventListener('click',()=>draw(b.dataset.loadMode)));draw('crowded');
})();

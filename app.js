const parts={
 ced:['CAUSAL ENCODER–DECODER','The encoder’s outputs become the decoder’s global KV cache.','The encoder processes the input through attention and expert layers. Its last layer produces a vector for each position. Learned projections turn those vectors into global keys and values that the decoder can read.','Input → encoder hidden-state vectors → decoder global keys and values.'],
 attention:['COMPRESSED SPARSE ATTENTION 2','CSA2 separates memory construction, selection, and attention.','Full layers build global keys and values. Reindex layers choose new entries from that memory. Reuse layers keep the preceding selection while each layer still computes its own attention output.','Connection: CSA2 layers read global memory and combine it with each layer’s local sliding-window cache.'],
 engram:['CONDITIONAL MEMORY','Engram retrieves learned vectors for short token groups.','Engram hashes groups of 2, 3, and 4 tokens into embedding tables. The retrieved memory is gated by the current hidden state before it is added to the model.','Connection: Engram feeds learned n-gram memory into selected encoder layers.'],
 dspark:['SPECULATIVE DECODING','DSpark drafts several future positions for faster generation.','The decoder supplies states to DSpark, which drafts five positions in parallel. A scheduler chooses how many positions to verify using predicted acceptance and serving throughput.','Connection: decoder states feed DSpark; verified draft tokens become generated output.']
};
const architectureOrder=['ced','attention','engram','dspark'];
function showArchitecturePart(name){
 const index=architectureOrder.indexOf(name),p=parts[name];
 document.querySelectorAll('[data-part]').forEach(x=>{const on=x.dataset.part===name;x.classList.toggle('selected',on);x.setAttribute('aria-pressed',String(on))});
 ['part-tag','part-title','part-body','part-connection'].forEach((id,i)=>document.getElementById(id).textContent=p[i]);
 document.querySelector('.architecture-stage').dataset.architectureFocus=name;
 document.getElementById('architecture-step').textContent=String(index+1);
 document.getElementById('architecture-prev').disabled=index===0;
 document.getElementById('architecture-next').disabled=index===architectureOrder.length-1;
}
document.querySelectorAll('[data-part]').forEach(b=>b.addEventListener('click',()=>showArchitecturePart(b.dataset.part)));
document.getElementById('architecture-prev')?.addEventListener('click',()=>{const current=document.querySelector('[data-part].selected')?.dataset.part||'ced';showArchitecturePart(architectureOrder[Math.max(0,architectureOrder.indexOf(current)-1)])});
document.getElementById('architecture-next')?.addEventListener('click',()=>{const current=document.querySelector('[data-part].selected')?.dataset.part||'ced';showArchitecturePart(architectureOrder[Math.min(architectureOrder.length-1,architectureOrder.indexOf(current)+1)])});
const modes={full:{ids:[2,5,7],title:'Build memory + select entries',body:'A Full layer constructs global KV and indexer keys, then chooses which entries its query will attend to.'},reindex:{ids:[1,4,8],title:'Same memory. New selection.',body:'A Reindex layer reuses the global KV and indexer keys from the most recent Full layer. Its own indexer query scores those keys and selects new entries.'},reuse:{ids:[1,4,8],title:'Same memory. Same selection.',body:'A Reuse layer keeps the shared global memory and the preceding index-producing layer’s selection. It still computes fresh attention using its own main query and local KV.'}};
const bank=document.getElementById('bank');for(let i=1;i<=8;i++){const e=document.createElement('span');e.className='entry';e.textContent=i;e.dataset.id=i;bank.append(e)}
function mode(name){const m=modes[name];document.querySelectorAll('[data-mode]').forEach(b=>{const on=b.dataset.mode===name;b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on))});bank.querySelectorAll('.entry').forEach(e=>e.classList.toggle('chosen',m.ids.includes(Number(e.dataset.id))));document.getElementById('selected-entries').replaceChildren(...m.ids.map(i=>{const s=document.createElement('span');s.textContent=i;return s}));document.getElementById('mode-title').textContent=m.title;document.getElementById('mode-body').textContent=m.body}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>mode(b.dataset.mode)));mode('full');
document.getElementById('owners').addEventListener('input',e=>{const n=Number(e.target.value);document.getElementById('owner-value').textContent=`${n} of 8`;document.getElementById('shared-bar').style.width=`${n/8*100}%`;document.getElementById('shared-units').textContent=`${n} unit${n===1?'':'s'}`;document.getElementById('saving').textContent=`${(1-n/8)*100}%`});
// Current reading position is maintained by course-contents.js.


// Completion is recorded only after a learner presses a task button or runs an exercise.
(()=>{
 const key='deepseek-course-tasks-v1',known=['architecture-tour','model-information','attention-designs','fp4-cache','swa-replay','expert-routing','single-pass-mhc','dspark','task-construction','read-ablation','trained-baseline','kv-cache-experiment','packed-offsets','engram-lab'];
 let completed=new Set();
 try{const saved=JSON.parse(localStorage.getItem(key)||'[]');if(Array.isArray(saved))completed=new Set(saved.filter(id=>known.includes(id)))}catch{}
 const lab=document.getElementById('engram-lab');
 if(lab&&!lab.querySelector('[data-task-id="engram-lab"]'))lab.insertAdjacentHTML('beforeend','<button class="task-complete" type="button" data-task-id="engram-lab">Mark runnable Engram lab complete</button>');
 const panel=document.createElement('div');panel.className='course-progress';panel.innerHTML='<div><small>YOUR PROGRESS</small><strong id="course-progress-count"></strong></div><a id="course-resume" href="#architecture">Resume next task ↓</a><button type="button" id="course-progress-reset">Reset</button>';
 document.querySelector('.hero-route')?.insertAdjacentElement('afterend',panel);
 function draw(){
  document.querySelectorAll('[data-task-id]').forEach(button=>{const done=completed.has(button.dataset.taskId);button.classList.toggle('is-complete',done);button.textContent=done?'✓ Task completed':button.dataset.taskId==='architecture-tour'?'Mark architecture tour complete':button.dataset.taskId==='engram-lab'?'Mark runnable Engram lab complete':'Mark task complete'});
  document.getElementById('course-progress-count').textContent=`${completed.size} of ${known.length} implemented tasks completed`;
  const next=known.find(id=>!completed.has(id)),resume=document.getElementById('course-resume');
  resume.href=['model-information','attention-designs','fp4-cache','swa-replay','expert-routing','single-pass-mhc','dspark','task-construction','read-ablation'].includes(next)?'#'+next:next==='trained-baseline'?'#trained-baseline':next==='kv-cache-experiment'?'#kv-cache-experiment':next==='architecture-tour'?'#architecture':next==='packed-offsets'?'#engram-code':next==='engram-lab'?'#engram-lab':'#start';resume.textContent=next?'Resume next task ↓':'All implemented tasks completed ✓';
  try{localStorage.setItem(key,JSON.stringify([...completed]))}catch{}
 }
 document.addEventListener('click',event=>{const button=event.target.closest('[data-task-id]');if(!button)return;completed.add(button.dataset.taskId);draw()});
 document.addEventListener('course-task-complete',event=>{if(known.includes(event.detail))completed.add(event.detail);draw()});
 document.getElementById('course-progress-reset').addEventListener('click',()=>{completed.clear();draw()});draw();
})();

(()=>{
 const reveal=document.getElementById('kv-reveal');if(!reveal)return;
 reveal.addEventListener('click',()=>{
  const memory=document.getElementById('kv-memory-prediction').value,time=document.getElementById('kv-time-prediction').value,feedback=document.getElementById('kv-prediction-feedback');
  if(!memory||!time){feedback.textContent='Choose both predictions before revealing the run.';return}
  const memoryText=memory==='double'?'Your memory prediction matches the tensor measurement.':'The measured KV tensor bytes doubled because each added position stores one key and one value.';
  const timeText=time==='increase'?'Your runtime prediction keeps measurement separate from theory.':'Runtime increased overall, but there is no exact factor promised by this small benchmark.';
  feedback.textContent=`${memoryText} ${timeText}`;feedback.classList.add('success');document.getElementById('kv-results').hidden=false;document.getElementById('kv-interpretation').hidden=false;
  document.dispatchEvent(new CustomEvent('course-task-complete',{detail:'kv-cache-experiment'}));
 });
})();

// The written lesson's causal n-gram windows; independent of video timing.
const ngramWords=['I','love','New','York','City'];
function showNgrams(position){
 document.querySelectorAll('[data-ngram-position]').forEach(button=>{
  const index=Number(button.dataset.ngramPosition);
  button.classList.toggle('selected',index===position);
  button.classList.toggle('ngram-future',index>position);
  button.setAttribute('aria-pressed',String(index===position));
 });
 document.getElementById('ngram-current').textContent=`Current position: ${ngramWords[position]}. ${position<4?'Tokens to its right are excluded.':'All groups now end at City.'}`;
 const rows=[2,3,4].map(n=>{
  const row=document.createElement('div');row.className='ngram-window';
  const label=document.createElement('b');label.textContent=`${n}-gram`;
  const group=document.createElement('div');
  for(let index=position-n+1;index<=position;index++){
   const token=document.createElement('span');token.textContent=index<0?'PAD':ngramWords[index];
   if(index<0)token.className='ngram-pad';group.append(token);
  }
  row.append(label,group);return row;
 });
 document.getElementById('ngram-windows').replaceChildren(...rows);
}
if(document.getElementById('ngram-windows')){
 document.querySelectorAll('[data-ngram-position]').forEach(button=>button.addEventListener('click',()=>showNgrams(Number(button.dataset.ngramPosition))));
 showNgrams(3);
}

// Keep off-screen playback discoverable without interrupting reading.
const courseVideos=Array.from(document.querySelectorAll('article video'));
const playbackDock=document.createElement('div');
playbackDock.className='playback-dock';
playbackDock.hidden=true;
playbackDock.setAttribute('role','region');
playbackDock.setAttribute('aria-label','Off-screen video controls');
playbackDock.innerHTML='<div class="playback-status">● VIDEO PLAYING</div><strong class="playback-title"></strong><span class="playback-time"></span><div class="playback-actions"><button type="button" class="playback-pause">Pause</button><button type="button" class="playback-return">Go to video ↑</button></div>';
document.body.append(playbackDock);
const videoVisibility=new Map();
let activeCourseVideo=null;
const lessonNames={start:'Course opening',memory:'Sharing memory',selection:'Select, then read',hierarchy:'Search less',engram:'Engram memory'};
function playbackTime(seconds){
 if(!Number.isFinite(seconds))return '—';
 return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')}`;
}
function updatePlaybackDock(){
 const video=activeCourseVideo;
 const show=!!video&&!video.paused&&!video.ended&&!videoVisibility.get(video)&&!document.fullscreenElement;
 playbackDock.hidden=!show;
 document.body.classList.toggle('has-playback-dock',show);
 if(!show)return;
 const section=video.closest('section');
 playbackDock.querySelector('.playback-title').textContent=video.closest('#engram-approved-opening')?'Engram: new opening':video.closest('#engram-part-2')?'Engram: phrase tokens vs memory':video.closest('#engram-part-3')?'Engram: one memory lookup':video.closest('#engram-part-4')?'Engram: collisions and hash heads':video.closest('#engram-part-5')?'Engram: context controls memory':lessonNames[section?.id]||video.getAttribute('aria-label')||'Course video';
 playbackDock.querySelector('.playback-time').textContent=`${playbackTime(video.currentTime)} / ${playbackTime(video.duration)}`;
}
const playbackObserver=new IntersectionObserver(entries=>{
 entries.forEach(entry=>videoVisibility.set(entry.target,entry.isIntersecting&&entry.intersectionRatio>=.35));
 updatePlaybackDock();
},{threshold:[0,.35]});
courseVideos.forEach(video=>{
 playbackObserver.observe(video);
 video.addEventListener('play',()=>{
  activeCourseVideo=video;
  courseVideos.forEach(other=>{if(other!==video&&!other.paused)other.pause()});
  updatePlaybackDock();
 });
 ['pause','ended','timeupdate','loadedmetadata'].forEach(event=>video.addEventListener(event,updatePlaybackDock));
});
document.addEventListener('fullscreenchange',updatePlaybackDock);
playbackDock.querySelector('.playback-pause').addEventListener('click',()=>activeCourseVideo?.pause());
playbackDock.querySelector('.playback-return').addEventListener('click',()=>{
 if(!activeCourseVideo)return;
 // The opening clip can also be hidden by its collapsed details panel.
 for(let parent=activeCourseVideo.parentElement;parent;parent=parent.parentElement){
  if(parent.tagName==='DETAILS')parent.open=true;
 }
 activeCourseVideo.setAttribute('tabindex','-1');
 activeCourseVideo.focus({preventScroll:true});
 activeCourseVideo.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});
});

// Six small checks. Completion is local to this browser; it never gates reading.
if(document.querySelector('.learning-path')){
 const progressKey='deepseek-ngram-checks-v1';
 let completed=new Set();
 try{const saved=JSON.parse(localStorage.getItem(progressKey)||'[]');if(Array.isArray(saved))completed=new Set(saved.filter(n=>Number.isInteger(n)&&n>=1&&n<=6))}catch{}
 const visited=new Set(completed.has(3)?[1,4]:[]);
 const explanations={1:'Correct. Engram is the module; an n-gram is a token group.',2:'Exactly. New is immediately before York, so New · York is the 2-gram.',5:'Yes: 3 × 8 = 24 row lookups per position in one Engram module.',6:'Correct. The lookup is local; the hidden state and attention can use broader context.'};
 function drawProgress(){
  document.getElementById('ngram-progress').value=completed.size;
  document.getElementById('ngram-progress-text').textContent=`${completed.size} of 6 checks completed`;
  document.querySelectorAll('[data-learning-step]').forEach(card=>{
   const done=completed.has(Number(card.dataset.learningStep));card.classList.toggle('is-complete',done);
   card.querySelector('.step-completion').textContent=done?'✓ Check completed':'Ready to try';
  });
  document.querySelectorAll('[data-progress-link]').forEach(link=>link.classList.toggle('is-complete',completed.has(Number(link.dataset.progressLink))));
  document.getElementById('ngram-finish').hidden=completed.size!==6;
  try{localStorage.setItem(progressKey,JSON.stringify([...completed]))}catch{}
 }
 function complete(step){completed.add(step);drawProgress()}
 function drawVisits(){
  for(const [pos,id,label] of [[4,'visited-city','City'],[1,'visited-love','love']]){
   const el=document.getElementById(id);el.textContent=`${visited.has(pos)?'✓':'○'} Try ${label}`;el.classList.toggle('done',visited.has(pos));
  }
 }
 document.querySelectorAll('.mini-check').forEach(check=>{
  check.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{
   check.querySelectorAll('button').forEach(b=>b.classList.remove('answer-correct','answer-retry'));
   const correct=button.dataset.correct==='true';button.classList.add(correct?'answer-correct':'answer-retry');
   const feedback=check.querySelector('.check-feedback');feedback.textContent=correct?explanations[check.dataset.check]:button.dataset.feedback;feedback.classList.toggle('success',correct);
   if(correct)complete(Number(check.dataset.check));
  }));
 });
 document.querySelectorAll('[data-ngram-position]').forEach(button=>button.addEventListener('click',()=>{
  const pos=Number(button.dataset.ngramPosition);visited.add(pos);drawVisits();
  const feedback=document.getElementById('window-feedback');
  if(visited.has(1)&&visited.has(4)){feedback.textContent='You saw both cases: the windows move right, and missing earlier tokens become PAD.';feedback.classList.add('success');complete(3)}
  else feedback.textContent=pos===4?'At City, every group now ends at City. Next try love.':pos===1?'At love, the longer windows need PAD. Next try City.':'Now try City and love to compare a full window with padding.';
 }));
 function selectHash(button,mark=true){
  document.querySelectorAll('[data-hash-pair]').forEach(b=>{b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button))});
  const [a,b]=button.dataset.hashPair.split(',').map(Number),row=(31*a+b)%101;
  document.getElementById('hash-row').textContent=row;
  const total=31*a+b;
  document.getElementById('hash-calculation').textContent=`31 × ${a} + ${b} = ${total} = ${Math.floor(total/101)} × 101 + ${row}`;
  document.getElementById('hash-vector').textContent=row===28?'[0.2, −0.5, 0.8]':'[−0.1, 0.7, 0.3]';
  const feedback=document.getElementById('hash-feedback');
  feedback.textContent=a===18?'The reversed group maps to row 24 instead of 28. Token order affects the address.':a===1?'These are still two different n-grams. Their calculations both leave remainder 28, so they share memory row 28 and retrieve its vector. This is a hash collision; see both calculations below.':'This pair always maps to row 28 in the toy table. Try reversing the IDs.';
  feedback.classList.toggle('success',a===18);
  if(mark&&a===18)complete(4);
 }
 document.querySelectorAll('[data-hash-pair]').forEach(b=>b.addEventListener('click',()=>selectHash(b)));
 document.getElementById('ngram-gate').addEventListener('input',e=>{
  const value=Number(e.target.value);document.getElementById('ngram-gate-value').textContent=value.toFixed(2);document.getElementById('gate-factor').textContent=value.toFixed(2);
  document.getElementById('gate-result').textContent='['+[2,-1,.5].map(x=>Number((x*value).toFixed(3))).join(', ')+']';
 });
 document.getElementById('reset-ngram-progress').addEventListener('click',()=>{
  completed.clear();visited.clear();drawProgress();drawVisits();
  document.querySelectorAll('.mini-check .check-feedback').forEach(el=>{el.textContent='';el.classList.remove('success')});
  document.querySelectorAll('.answer-correct,.answer-retry').forEach(el=>el.classList.remove('answer-correct','answer-retry'));
  const message=document.getElementById('window-feedback');message.textContent='';message.classList.remove('success');
  selectHash(document.querySelector('[data-hash-pair="72,18"]'),false);
 });
 drawProgress();drawVisits();
}

// A manual teaching control, not a model-computed gate.
(()=>{
 const slider=document.getElementById('memory-gate');if(!slider)return;
 function update(){
  const g=Number(slider.value)/100,fmt=n=>Math.abs(n)<.005?'0.00':n.toFixed(2);
  document.getElementById('memory-gate-number').textContent=fmt(g);
  document.getElementById('gate-factor').textContent=fmt(g);
  document.getElementById('gate-update').textContent=`[${fmt(2*g)}, ${fmt(-g)}]`;
  document.getElementById('gate-state').textContent=`[${fmt(.5+2*g)}, ${fmt(.5-g)}]`;
 }
 slider.addEventListener('input',update);update();
})();

// A short visual bridge from the forward pass to the cache benchmark.
(()=>{
 const steps=[
  ['Read [12, 37, 9]','None yet','Positions 0, 1, 2','Save three keys and three values. The final prompt position produces scores for the next token.','Cache after this step: 3 positions.'],
  ['Append token 21 at position 3','Positions 0, 1, 2','Position 3 only','Compute the new query, key, and value. The query reads all four cached positions to score the following token. Earlier keys and values are not recomputed.','Cache after this step: 4 positions.'],
  ['Append token 6 at position 4','Positions 0, 1, 2, 3','Position 4 only','Reuse four earlier key/value pairs and add the new pair. The new query reads five positions. We save repeated computation, while the cache continues to grow.','Cache after this step: 5 positions.']
 ];
 document.querySelectorAll('[data-cache-stage]').forEach(button=>button.addEventListener('click',()=>{
  const selected=Number(button.dataset.cacheStage);
  document.querySelectorAll('[data-cache-stage]').forEach(b=>{const active=b===button;b.setAttribute('aria-pressed',String(active));b.classList.toggle('selected',active)});
  ['cache-stage-title','cache-stage-reused','cache-stage-new','cache-stage-body','cache-stage-size'].forEach((id,i)=>document.getElementById(id).textContent=steps[selected][i]);
 }));
})();

(()=>{
 'use strict';
 // Heading links own scroll restoration; browser history must not restore a stale pixel offset after responsive reflow.
 if('scrollRestoration' in history)history.scrollRestoration='manual';
 const nav=document.querySelector('#course-contents'),sidebar=document.querySelector('body>aside');if(!nav)return;
 const groups=[
 ['Start here','Architecture and information flow',['start','roadmap','architecture','model-information']],
 ['Attention and KV cache','Storage, sharing, selection and replay',['kv-cache-explanation','attention-designs','fp4-cache','memory','shared-query-example','selection','hierarchy','swa-replay']],
 ['Experts and residual streams','Which networks run; how their states combine',['expert-routing','single-pass-mhc']],
 ['Engram memory','N-grams, lookup tables, collisions and gates',['engram']],
 ['Drafting and training tasks','Propose tokens; verify outputs and code',['dspark','task-construction']],
 ['Read the research evidence','Reported results and controlled comparisons',['read-ablation']],
 ['Code and experiments','Inspect code, train a baseline and measure',['starting-model','trained-baseline','kv-cache-experiment','engram-lab','engram-research','experiment']],
 ['Review and next steps','Check understanding and choose a next build',['course-next']]
 ];
 const labels={'engram-research':'Compare n-gram memory with LoRA','start':'Course introduction','roadmap':'Learning path','architecture':'How the main components connect','model-information':'Weights, hidden states and caches','kv-cache-explanation':'Why earlier keys and values can be reused','attention-designs':'Compression, sharing and sparse selection','fp4-cache':'FP4 rounding and shared scales','memory':'Full, Reindex and Reuse layers','shared-query-example':'Different queries read the same cache','selection':'From indexer scores to attention','hierarchy':'Select blocks before selecting entries','swa-replay':'Rebuild missing local cache','expert-routing':'Select experts and combine their outputs','single-pass-mhc':'Mix residual streams in one pass','engram':'N-gram lookup and context gates','dspark':'Draft and verify several tokens','task-construction':'Build training tasks with reliable checks','read-ablation':'Interpret the reported benchmarks','starting-model':'Trace the attention code','trained-baseline':'Train and inspect a small language model','kv-cache-experiment':'Measure cache size and generation time','engram-lab':'Run the illustrative Engram lab','experiment':'Calculate cache storage','course-next':'Review what you learned'};
 const targets=[],links=[],branches=[],headingLinks=[];
 function link(target,label,kind){const a=document.createElement('a');a.href='#'+target.id;a.textContent=label;a.className='toc-link toc-'+kind;links.push(a);targets.push({target,link:a});return a}
 nav.replaceChildren();
 groups.forEach(([name,subtitle,ids],index)=>{
  const chapter=document.createElement('details');chapter.className='toc-chapter';branches.push(chapter);
  const summary=document.createElement('summary'),number=document.createElement('small'),title=document.createElement('strong'),sub=document.createElement('span');
  number.textContent=String(index+1).padStart(2,'0');title.textContent=name;sub.textContent=subtitle;summary.append(number,title,sub);chapter.append(summary);
  ids.forEach(id=>{
   const section=document.getElementById(id);if(!section)return;
   const lesson=document.createElement('div');lesson.className='toc-lesson';const a=link(section,labels[id]||id,'lesson-link');lesson.append(a);
   const headings=id==='start'||id==='roadmap'?[]:[...section.querySelectorAll('h3[data-edit-id]')];
   if(headings.length){
    const steps=document.createElement('details');steps.className='toc-steps';branches.push(steps);
    const s=document.createElement('summary');s.textContent='Lesson steps';s.setAttribute('aria-label','Show steps: '+labels[id]);steps.append(s);
    headings.forEach(h=>{if(!h.id)h.id='toc-'+h.dataset.editId;const child=link(h,h.textContent.trim(),'step-link');child.title=h.textContent.trim();steps.append(child);headingLinks.push({heading:h,link:child});});lesson.append(steps);
   }
   chapter.append(lesson);
  });
  if(chapter.querySelector('a'))nav.append(chapter);
 });
 // Keep the table of contents aligned with saved or live author edits.
 headingLinks.forEach(({heading,link:a})=>new MutationObserver(()=>{a.textContent=heading.textContent.trim();a.title=a.textContent}).observe(heading,{childList:true,characterData:true,subtree:true}));
 const search=document.getElementById('lesson-search'),status=document.getElementById('lesson-search-status');let beforeSearch=null;
 function filter(){
  const terms=search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  if(terms.length&&!beforeSearch)beforeSearch=new Map(branches.map(d=>[d,d.open]));
  let matches=0;
  nav.querySelectorAll('.toc-chapter').forEach(chapter=>{
   const chapterText=chapter.querySelector('summary').textContent;
   chapter.querySelectorAll('.toc-lesson').forEach(lesson=>{
    const main=lesson.querySelector('a'),all=[...lesson.querySelectorAll('a')];let found=false;
    all.forEach(a=>{const hay=(chapterText+' '+main.textContent+' '+a.textContent+' '+a.hash.replaceAll('-',' ')).toLowerCase();const hit=terms.every(t=>hay.includes(t));a.hidden=!hit;if(hit){matches++;found=true}});
    lesson.hidden=!found;if(found)main.hidden=false;
    const steps=lesson.querySelector('details');if(steps){steps.hidden=terms.length>0&&![...steps.querySelectorAll('a')].some(a=>!a.hidden);if(terms.length&& !steps.hidden)steps.open=true}
   });
   chapter.hidden=![...chapter.querySelectorAll('.toc-lesson')].some(l=>!l.hidden);if(terms.length&&!chapter.hidden)chapter.open=true;
  });
  if(!terms.length&&beforeSearch){beforeSearch.forEach((open,d)=>d.open=open);beforeSearch=null}
  status.hidden=!terms.length;status.textContent=matches?`${matches} matching lesson or step links`:'No match. Try cache, experts, or training.';
 }
 search.addEventListener('input',filter);
 const toggle=document.getElementById('toc-mobile-toggle');
 function closeMenu(){sidebar.classList.remove('toc-mobile-open');toggle.setAttribute('aria-expanded','false')}
 toggle.addEventListener('click',()=>{const open=sidebar.classList.toggle('toc-mobile-open');toggle.setAttribute('aria-expanded',String(open))});
 document.getElementById('toc-expand').addEventListener('click',()=>branches.forEach(d=>{if(!d.hidden)d.open=true}));
 document.getElementById('toc-collapse').addEventListener('click',()=>branches.forEach(d=>d.open=false));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sidebar.classList.contains('toc-mobile-open')){closeMenu();toggle.focus()}});
 let pinnedTarget=null;
 function land(target){pinnedTarget=target;if(target)target.scrollIntoView({block:'start',behavior:'instant'})}
 // Videos and saved text can finish loading after the anchor is reached. Keep that heading in place until the reader starts scrolling.
 const release=()=>{pinnedTarget=null};
 window.addEventListener('wheel',release,{passive:true});window.addEventListener('touchmove',release,{passive:true});
 window.addEventListener('keydown',e=>{if(['ArrowDown','ArrowUp','PageDown','PageUp','Home','End',' '].includes(e.key)&&!sidebar.contains(e.target))release()});
 document.addEventListener('pointerdown',e=>{if(!sidebar.contains(e.target)&&!e.target.closest('.course-editor'))release()});
 new ResizeObserver(()=>{if(pinnedTarget)land(pinnedTarget)}).observe(document.querySelector('main>article'));
 function revealTarget(hash){let id;try{id=decodeURIComponent(hash.slice(1))}catch{return}const target=document.getElementById(id);if(!target)return;let p=target.parentElement;while(p){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement}return target}
 nav.addEventListener('click',e=>{const a=e.target.closest('a');if(!a||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;const target=revealTarget(a.hash);if(!target)return;e.preventDefault();history.pushState(null,'',a.hash);closeMenu();land(target);schedule()});
 let active=null,queued=false;
 const ordered=[...targets].sort((a,b)=>a.target===b.target?0:a.target.compareDocumentPosition(b.target)&Node.DOCUMENT_POSITION_FOLLOWING?-1:1);
 function locate(){queued=false;let current=ordered[0];for(const row of ordered){if(!row.target.getClientRects().length)continue;if(row.target.getBoundingClientRect().top<=240)current=row;else break}if(!current||active===current)return;active=current;
  links.forEach(a=>{const on=a===current.link;a.classList.toggle('active',on);if(on)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')});
  nav.querySelectorAll('.toc-chapter,.toc-lesson').forEach(e=>e.classList.toggle('toc-current-branch',e.contains(current.link)));
  if(!search.value.trim()){let p=current.link.parentElement;while(p&&p!==nav){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement}}
  document.getElementById('toc-current').textContent=current.link.textContent;
 }
 function schedule(){if(!queued){queued=true;requestAnimationFrame(locate)}}
 window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);
 window.addEventListener('hashchange',()=>{const target=revealTarget(location.hash);if(target)land(target);schedule()});
 const initial=revealTarget(location.hash);if(initial)land(initial);locate();
 window.addEventListener('load',()=>{const target=revealTarget(location.hash);if(target)land(target);schedule()},{once:true});
})();

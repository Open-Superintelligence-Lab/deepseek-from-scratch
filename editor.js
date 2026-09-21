(async()=>{
 const fields=[...document.querySelectorAll('[data-edit-id]')];
 const originals=new Map(fields.map(el=>[el.dataset.editId,el.textContent]));
 const byId=new Map(fields.map(el=>[el.dataset.editId,el]));
 // Public readers get saved article text without local author controls or API calls.
 const localAuthor=['localhost','127.0.0.1',''].includes(location.hostname);
 if(!localAuthor){
  document.body.classList.add('learner-view');
  try{const r=await fetch('content/text-edits.json');if(r.ok){const data=await r.json();Object.entries(data.edits||{}).forEach(([id,text])=>{const el=byId.get(id);if(el)el.textContent=text})}}catch{}
  return;
 }
 const bar=document.createElement('div');bar.className='course-editor';bar.innerHTML='<div class="view-switch" role="group" aria-label="Course view"><button type="button" data-view="learner">Learner view</button><button type="button" data-view="author">Author view</button></div><div class="author-tools"><button type="button" id="toggle-edit" aria-pressed="false">Edit text</button><span role="status" id="edit-status">Loading saved text…</span><button type="button" id="export-text">Export text</button></div>';
 document.body.append(bar);
 const status=bar.querySelector('#edit-status'),toggle=bar.querySelector('#toggle-edit'),viewKey='deepseek-course-view-v1';
 const storageKey='deepseek-course-pending-edits-v1';let pending={},saved={},editing=false,working=false,timer;
 function setView(view){
  if(view!=='learner'&&view!=='author')view='author';
  if(view==='learner'&&editing){editing=false;document.body.classList.remove('editing-text');toggle.textContent='Edit text';toggle.setAttribute('aria-pressed','false');fields.forEach(el=>{el.contentEditable='false';el.removeAttribute('aria-label')})}
  document.body.classList.toggle('learner-view',view==='learner');document.body.classList.toggle('author-view',view==='author');
  bar.querySelectorAll('[data-view]').forEach(button=>{const on=button.dataset.view===view;button.classList.toggle('selected',on);button.setAttribute('aria-pressed',String(on))});
  try{localStorage.setItem(viewKey,view)}catch{}
 }
 bar.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>setView(button.dataset.view)));
 let initialView='author';try{initialView=localStorage.getItem(viewKey)||'author'}catch{}setView(initialView);
 try{pending=JSON.parse(localStorage.getItem(storageKey)||'{}')}catch{}
 function recovery(){try{localStorage.setItem(storageKey,JSON.stringify(pending))}catch{status.textContent='Save unavailable — keep this page open';}}
 function markChanged(el){
  const card=el.closest('#engram-script');if(!card)return;
  const changed=[...card.querySelectorAll('[data-edit-id]')].some(n=>n.textContent!==originals.get(n.dataset.editId));
  card.classList.toggle('script-edited',changed);
  card.querySelector('.approval-badge').textContent=changed?'Approved video · Text edited':'✓ Fully approved · Text + video';
 }
 function apply(id,text){const el=byId.get(id);if(el){el.textContent=text;markChanged(el)}}
 try{
  const r=await fetch('/api/text-edits');if(!r.ok)throw Error();saved=(await r.json()).edits||{};
  Object.entries(saved).forEach(([id,text])=>apply(id,text));status.textContent='Edits save to this course folder';
 }catch{status.textContent='Save server offline — edits kept in this browser';}
 Object.entries(pending).forEach(([id,text])=>apply(id,text));
 async function flush(){
  if(working)return;working=true;
  try{
   while(Object.keys(pending).length){
    const id=Object.keys(pending)[0],text=pending[id];
    status.textContent='Saving…';
    const r=await fetch('/api/text-edits',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,text})});
    if(!r.ok)throw Error();await r.json();saved[id]=text;
    if(pending[id]===text)delete pending[id];recovery();
   }
   status.textContent='Saved to course folder';
  }catch{status.textContent='Not saved to disk — local copy kept. Retrying…';setTimeout(flush,4000)}
  finally{working=false}
 }
 fields.forEach(el=>{
  el.addEventListener('input',()=>{pending[el.dataset.editId]=el.innerText;recovery();markChanged(el);status.textContent='Unsaved changes…';clearTimeout(timer);timer=setTimeout(flush,400)});
  el.addEventListener('blur',()=>{if(Object.keys(pending).length)flush()});
 });
 toggle.addEventListener('click',()=>{
  editing=!editing;document.body.classList.toggle('editing-text',editing);toggle.textContent=editing?'Done editing':'Edit text';toggle.setAttribute('aria-pressed',String(editing));
  fields.forEach(el=>{el.contentEditable=editing?'plaintext-only':'false';if(editing)el.setAttribute('aria-label','Edit '+(originals.get(el.dataset.editId)||'text').slice(0,70));else el.removeAttribute('aria-label')});
  if(!editing&&Object.keys(pending).length)flush();
 });
 bar.querySelector('#export-text').addEventListener('click',()=>{
  const content=fields.map(el=>el.innerText).join('\n\n');const url=URL.createObjectURL(new Blob([content],{type:'text/plain'}));const a=document.createElement('a');a.href=url;a.download='deepseek-course-text.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 document.addEventListener('keydown',e=>{if((e.metaKey||e.ctrlKey)&&e.key==='s'){e.preventDefault();flush()}});
 window.addEventListener('beforeunload',e=>{if(Object.keys(pending).length){e.preventDefault();e.returnValue=''}});
 if(Object.keys(pending).length)flush();
})();

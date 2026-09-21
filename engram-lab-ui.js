(()=>{
'use strict';
const E=window.ToyEngram, $=id=>document.getElementById(id);
if(!$('engram-lab'))return;
let tokens=E.tokenize($('el-sentence').value),position=3,order=2,memory;
const fmt=v=>'['+v.map(x=>x.toFixed(3)).join(', ')+']';
function el(tag,text,className){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;}
function renderInput(){
 const buttons=tokens.map((token,i)=>{const b=el('button',token.word);b.type='button';b.classList.toggle('selected',i===position);b.classList.toggle('future',i>position);b.setAttribute('aria-pressed',String(i===position));b.setAttribute('aria-label',`Process ${token.word}, position ${i+1}`);b.addEventListener('click',()=>{position=i;renderInput();renderMemory()});return b;});
 $('el-tokens').replaceChildren(...buttons);
 $('el-groups').replaceChildren(...E.groups(tokens,position).map(group=>{const b=el('button');b.type='button';b.classList.toggle('selected',group.n===order);b.setAttribute('aria-pressed',String(group.n===order));b.append(el('strong',`${group.n}-gram`),el('span',group.words.join(' · ')),el('small',`IDs: [${group.ids.join(', ')}]`));b.addEventListener('click',()=>{order=group.n;renderInput();renderMemory()});return b;}));
}
function renderMemory(){
 const heads=+$('el-heads').value,rows=+$('el-rows').value;
 memory=E.retrieve(E.groups(tokens,position),heads,rows);
 const chosen=memory.groups.find(g=>g.n===order);
 $('el-selected').textContent=`Inspecting the ${order}-gram: ${chosen.words.join(' · ')}`;
 $('el-hash-formula').textContent='Toy hash: start at 0; for each ID, update row = (base × row + ID) mod table size. Head bases: '+Array.from({length:heads},(_,h)=>31+2*h).join(', ')+'.';
 $('el-lookups').replaceChildren(...chosen.lookups.map(h=>{const card=el('div');card.append(el('small',`HEAD ${h.head+1}`),el('strong',`Row ${h.row}`),el('code',fmt(h.vector)));return card;}));
 $('el-count').textContent=`${heads*3} row lookups × 3 numbers = ${heads*9} numbers concatenated. Fixed random projections produce the key and value below.`;
 $('el-key').textContent=fmt(memory.key);$('el-value').textContent=fmt(memory.value);renderGate();
}
function renderGate(){const angle=+$('el-context').value,g=E.contextGate(memory.key,memory.value,angle);$('el-angle').textContent=angle+'°';$('el-gate').textContent=g.gate.toFixed(3);$('el-gate-bar').style.width=(g.gate*100)+'%';$('el-hidden').textContent=fmt(g.hidden);$('el-added').textContent=fmt(g.added);$('el-output').textContent=fmt(g.output);$('el-gate-summary').textContent=`The retrieved key and value stay fixed as you move this slider. This hidden state lets through ${(g.gate*100).toFixed(1)}% of the value.`;document.querySelectorAll('[data-el-context]').forEach(b=>{b.classList.toggle('selected',+b.dataset.elContext===angle);b.setAttribute('aria-pressed',String(+b.dataset.elContext===angle))});}
function renderCollisions(){const rows=+$('el-collision-rows').value,result=E.collisionExperiment(rows);
 $('el-collision-stats').replaceChildren(...[result.one,result.eight].map(m=>{const card=el('div');card.append(el('small',m.heads===1?'ONE HEAD':'EIGHT HEADS'),el('strong',`${m.distinct} / 256`),el('p','distinct address patterns'),el('span',`${m.sharedGroups} input groups share their full address pattern with at least one other group.`),el('small',`${rows*m.heads} table rows total · ${rows*m.heads*3} stored numbers`));return card;}));
 const table=el('table'),caption=el('caption','Computed addresses for two different pairs. H1–H8 are separate hash heads.');table.append(caption);const thead=el('thead'),tr=el('tr');tr.append(el('th','Input pair'));for(let h=0;h<8;h++)tr.append(el('th','H'+(h+1)));thead.append(tr);table.append(thead);const tbody=el('tbody');for(let k=0;k<2;k++){const tr=el('tr');tr.append(el('th','['+result.example[k].join(', ')+']'));result.addresses[k].forEach((a,h)=>{const cell=el('td',String(a));cell.className=result.addresses[0][h]===result.addresses[1][h]?'same-address':'different-address';tr.append(cell)});tbody.append(tr)}table.append(tbody);$('el-collision-example').replaceChildren(table);
 const separates=result.addresses[0].join()!=result.addresses[1].join();$('el-collision-insight').textContent=separates?'Gold cells share an address within that head. Blue cells differ: these groups collide in head 1, but other heads separate them.':'These two groups share every displayed address. Even eight heads did not separate them with this table size and hash. Try 17 rows.';
}
$('el-form').addEventListener('submit',event=>{event.preventDefault();const next=E.tokenize($('el-sentence').value);if(!next.length){$('el-input-status').textContent='Enter at least one word. The previous result remains below.';$('el-sentence').setAttribute('aria-invalid','true');return;}$('el-sentence').removeAttribute('aria-invalid');tokens=next;position=Math.min(position,tokens.length-1);$('el-input-status').textContent=`Running ${tokens.length} toy tokens. `+($('el-sentence').value.trim().split(/\s+/u).length>32?'Only the first 32 are used.':'Choose a token below.');renderInput();renderMemory()});
['el-heads','el-rows'].forEach(id=>$(id).addEventListener('change',renderMemory));$('el-context').addEventListener('input',renderGate);document.querySelectorAll('[data-el-context]').forEach(b=>b.addEventListener('click',()=>{$('el-context').value=b.dataset.elContext;renderGate()}));$('el-collision-rows').addEventListener('change',renderCollisions);
renderInput();renderMemory();renderCollisions();
})();

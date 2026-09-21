(()=>{
  const root=document.querySelector('#attention-designs');
  if(!root)return;
  const modes={
    baseline:{label:'BASELINE / STORE AND READ EVERYTHING',title:'Four layers each keep a full global cache.',body:'Each layer stores 8 positions as a toy K-and-V pair: 8 × 2 vectors × 8 values × 2 bytes = 256 bytes. Four independent owners store 1,024 bytes. Each query reads all 8 global positions.',storage:'1,024 B',storageWidth:'100%',read:'8 of 8',readWidth:'100%',owners:['own cache','own cache','own cache','own cache'],reads:'reads 8 global entries',result:'Nothing yet. This gives the reference count for the three choices.'},
    compress:{label:'1 / COMPRESS THE REPRESENTATION',title:'Keep the same owners, but make each global item smaller.',body:'For this toy comparison, replace the 32-byte K-and-V pair with one 16-byte latent entry at each of 8 positions. Four layers now store 512 bytes. The number of global positions read remains 8.',storage:'512 B',storageWidth:'50%',read:'8 of 8',readWidth:'100%',owners:['compact cache','compact cache','compact cache','compact cache'],reads:'reads 8 global entries',result:'Compression changes bytes per stored item. It does not by itself share a cache or shrink the read set.'},
    share:{label:'2 / SHARE GLOBAL MEMORY',title:'One owner publishes the same full toy global memory for four layers.',body:'This tab isolates sharing: one owner stores the 256-byte toy cache and the other three layers read the compatible global memory. Global storage is 256 bytes rather than 1,024 bytes. Each layer can still read 8 global entries.',storage:'256 B',storageWidth:'25%',read:'8 of 8',readWidth:'100%',owners:['owner: 256 B','reads owner','reads owner','reads owner'],reads:'reads 8 global entries',result:'Sharing changes the number of global-cache owners. It does not mean the layers share queries, local-window KV, or outputs.'},
    select:{label:'3 / SELECT FEWER ENTRIES TO READ',title:'Keep all four independent caches, then give attention three global addresses.',body:'This tab isolates selection: every layer still owns its 256-byte, 8-entry toy cache, so global storage remains 1,024 bytes. An indexer proposes a Top-3 set for the main attention read.',storage:'1,024 B',storageWidth:'100%',read:'3 of 8',readWidth:'37.5%',owners:['own cache','own cache','own cache','own cache'],reads:'reads Top-3 addresses',result:'Selection changes which global entries main attention reads. It does not delete the unselected entries or prove a runtime gain.'}
  };
  const get=id=>root.querySelector('#'+id);
  function draw(name){
    const m=modes[name];if(!m)return;
    root.querySelectorAll('[data-design-mode]').forEach(button=>{const active=button.dataset.designMode===name;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1});
    get('design-panel').setAttribute('aria-labelledby','design-tab-'+name);
    get('design-stage-label').textContent=m.label;get('design-stage-title').textContent=m.title;get('design-stage-body').textContent=m.body;
    get('design-storage').textContent=m.storage;get('design-storage-bar').style.width=m.storageWidth;get('design-read').textContent=m.read;get('design-read-bar').style.width=m.readWidth;
    get('design-layer-row').replaceChildren(...m.owners.map((owner,index)=>{const layer=document.createElement('div');layer.className='design-layer';layer.innerHTML='<strong>Layer '+(index+1)+'</strong><span class="design-owner">'+owner+'</span><span class="design-read-mark">'+m.reads+'</span>';return layer}));
    get('design-result').textContent=m.result;
  }
  const tabs=[...root.querySelectorAll('[data-design-mode]')];
  tabs.forEach((button,index)=>{button.addEventListener('click',()=>draw(button.dataset.designMode));button.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].focus();draw(tabs[next].dataset.designMode)})});
  draw('baseline');
})();

(()=>{
  const root=document.getElementById('swa-replay-demo'); if(!root)return;
  const prefixLength=8, localLayers=4;
  const windowInput=root.querySelector('#swa-window');
  const buttons=[...root.querySelectorAll('[data-swa-stage]')];
  const row=root.querySelector('#swa-token-row');
  const copy={
    save:{label:'1 / SAVE THE FIRST TURN',title:'The prefix creates global and local state.',body:'A completed prefix produces global KV plus local SWA KV. The local part can serve the active conversation, but is not chosen for long-lived persistent storage.',store:'Global KV: positions 0–7',runtime:w=>'SWA KV: last '+w+' positions (active only)',feedback:w=>'The first turn has both kinds of state. This lesson’s toy keeps global KV persistently and treats the local '+w+'-position state as short-lived.'},
    load:{label:'2 / A LATER TURN LOADS THE PREFIX',title:'A persistent hit restores global context without local KV.',body:'The system finds the old prefix’s global KV. The short-lived local state is absent, so continuing immediately would miss the SWA state needed by the local layers.',store:'Global KV: loaded for positions 0–7',runtime:'SWA KV: missing at cache hit',feedback:w=>'The global cache hit is useful across turns. Saving every layer’s local '+w+'-position state persistently would avoid this miss, but adds storage with a poor long-retention reuse pattern.'},
    replay:{label:'3 / BOUND THE LOCAL REBUILD',title:'Replay only the recent suffix and truncate local attention at its edge.',body:'Replay the last selected positions. Their global KV is reused; local SWA KV is regenerated. Positions before the replay start are deliberately outside this local pass.',store:'Global KV: reused, not overwritten',runtime:w=>'SWA KV: regenerated for last '+w+' positions',feedback:w=>{const theoretical=localLayers*w,exact=Math.min(prefixLength,theoretical);return 'Bounded replay recomputes '+w+' toy positions. The theoretical stacked span is '+localLayers+' × '+w+' = '+theoretical+' positions, but this prefix contains only '+prefixLength+'. Exact recovery would therefore replay all '+exact+' available prefix positions. The shorter path is approximate.';}},
    continue:{label:'4 / CONTINUE THE NEW TURN',title:'New suffix tokens create fresh global and local entries.',body:'The replayed local state supports continuation. New uncached tokens generate both cache kinds, but their states inherit the bounded replay boundary and are not mathematically identical to a full-prefix run.',store:'Global KV: old positions reused; new suffix appended',runtime:w=>'SWA KV: replayed '+w+' positions + new suffix',feedback:w=>'This mirrors the encoder idea at a high level: reuse global state, replay a bounded local suffix, then continue. The decoder has a separate bounded path to make decoder SWA KV for decoding.'}
  };
  let stage='save';
  const text=id=>root.querySelector(id);
  function render(){
    const w=Number(windowInput.value), state=copy[stage], start=prefixLength-w;
    const theoretical=localLayers*w, exact=Math.min(prefixLength,theoretical);
    text('#swa-window-value').textContent=w+' position'+(w===1?'':'s');
    text('#swa-stage-label').textContent=state.label;
    text('#swa-stage-title').textContent=state.title;
    text('#swa-stage-body').textContent=state.body;
    text('#swa-store-status').textContent=state.store;
    text('#swa-runtime-status').textContent=typeof state.runtime==='function'?state.runtime(w):state.runtime;
    text('#swa-persistent-local').textContent='0 positions';
    text('#swa-bounded-count').textContent=w+' positions';
    text('#swa-exact-count').textContent='min('+prefixLength+', '+localLayers+' × '+w+') = '+exact+' positions';
    text('#swa-theoretical-span').textContent=localLayers+' × '+w+' = '+theoretical+' positions';
    text('#swa-demo-feedback').textContent=state.feedback(w);
    row.replaceChildren(...Array.from({length:prefixLength},(_,i)=>{
      const token=document.createElement('div'); token.className='swa-token';
      if((stage==='replay'||stage==='continue')&&i>=start) token.classList.add('is-recomputed');
      if((stage==='replay'||stage==='continue')&&i<start) token.classList.add('is-excluded');
      token.innerHTML='<small>POSITION</small><strong>'+i+'</strong>';
      return token;
    }));
    buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.swaStage===stage)));
  }
  buttons.forEach(button=>button.addEventListener('click',()=>{stage=button.dataset.swaStage;render();}));
  windowInput.addEventListener('input',render); render();
})();

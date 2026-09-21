(() => {
  const root = document.querySelector('[data-info-walkthrough]');
  const prediction = document.querySelector('.info-prediction');
  if (prediction) {
    const feedback = prediction.querySelector('#info-prediction-feedback');
    const reveal = document.querySelector('#info-prediction-reveal');
    prediction.querySelectorAll('[data-info-answer]').forEach((button) => {
      button.addEventListener('click', () => {
        const correct = button.dataset.infoAnswer === 'request';
        prediction.querySelectorAll('[data-info-answer]').forEach((item) => item.classList.remove('is-right', 'is-wrong'));
        button.classList.add(correct ? 'is-right' : 'is-wrong');
        feedback.textContent = correct ? 'Yes. Now reveal why.' : 'Almost. Ask whether the numbers were learned during training or calculated from this request.';
        if (correct) reveal.hidden = false;
      });
    });
  }
  if (!root) return;
  const stages = [
    { kicker: 'STEP 1 / INPUT BECOMES VECTORS', title: 'Look up learned token embeddings', body: 'The token IDs select learned embedding rows. The resulting vectors are new temporary states for this sequence. The released implementation applies rotary position information later inside attention projections; this card does not depict an added position-embedding vector.', request: 'Input activation vectors', learned: 'Embedding table', active: [0, 1, 2] },
    { kicker: 'STEP 2 / ENCODER CONDITIONAL MEMORY', title: 'Engram retrieves inside the encoder', body: 'At its configured encoder layers, Engram uses short token groups to address learned table rows. The current hidden state gates their contribution while the encoder continues processing the prompt. The table is learned; the addresses and gates depend on this input.', request: 'Addresses and gate values', learned: 'Engram embedding table', active: [1, 2] },
    { kicker: 'STEP 3 / FINISH THE ENCODER', title: 'The encoder produces final hidden states', body: 'Encoder layers transform each position while respecting causal order. The final encoder hidden state for a position is a context-dependent vector: changing an earlier token can change later states.', request: 'Final encoder states', learned: 'Encoder weights', active: [0, 1, 2] },
    { kicker: 'STEP 4 / PREPARE GLOBAL CONTEXT', title: 'Project decoder global KV from final encoder states', body: 'For each decoder layer’s global attention, learned projection weights turn final encoder states into cache entries. CSA2 can share that global KV and indexer keys across selected decoder layers. The entries depend on this prompt; the projection weights do not.', request: 'Decoder global K/V', learned: 'Layer-dependent projections', active: [0, 1, 2] },
    { kicker: 'STEP 5 / KEEP A SEPARATE LOCAL WINDOW', title: 'Generate local KV from each decoder layer’s own state', body: 'Sliding-window attention is different: its local keys and values are derived layer by layer from the current hidden states. They support nearby context and are separate from the global KV path.', request: 'Layer-local SWA K/V', learned: 'Local attention projections', active: [2] },
    { kicker: 'STEP 6 / SCORE ONE CONTINUATION', title: 'The decoder state produces next-token scores', body: 'The decoder combines its computations to produce scores over possible next tokens. Sampling or selection chooses a token, which begins a new incremental step. The growing cache lets that new step read the old sequence.', request: 'Next-token scores and cache', learned: 'Output projection', active: [2] }
  ];
  let index = 0;
  const byId = (id) => root.querySelector(id);
  const tabs = [...root.querySelectorAll('[data-info-step]')];
  const update = (next) => {
    index = Math.max(0, Math.min(stages.length - 1, next));
    const stage = stages[index];
    byId('#info-step-kicker').textContent = stage.kicker;
    byId('#info-step-title').textContent = stage.title;
    byId('#info-step-body').textContent = stage.body;
    byId('#info-step-request').textContent = stage.request;
    byId('#info-step-learned').textContent = stage.learned;
    byId('#info-step-count').textContent = `${index + 1} / ${stages.length}`;
    byId('[data-info-prev]').disabled = index === 0;
    byId('[data-info-next]').disabled = index === stages.length - 1;
    tabs.forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
    root.querySelector('#info-step-panel').setAttribute('aria-labelledby', `info-step-tab-${index}`);
    root.querySelectorAll('.info-sequence span').forEach((token, i) => token.classList.toggle('is-active', stage.active.includes(i)));
  };
  tabs.forEach((tab) => tab.addEventListener('click', () => update(Number(tab.dataset.infoStep))));
  byId('[data-info-prev]').addEventListener('click', () => update(index - 1));
  byId('[data-info-next]').addEventListener('click', () => update(index + 1));
  root.querySelector('.info-walkthrough-tabs').addEventListener('keydown', (event) => {
    if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? stages.length - 1 : index + (event.key === 'ArrowRight' ? 1 : -1);
    update(next); tabs[index].focus();
  });
})();

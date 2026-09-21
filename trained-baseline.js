(() => {
 'use strict';
 const host=document.getElementById('baseline-recorded-run');
 if(!host)return;
 const el=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
 fetch('content/trained-baseline-run.json').then(r=>{if(!r.ok)throw Error('Saved measurements unavailable');return r.json();}).then(run=>{
  const metrics=el('div',undefined,'baseline-metrics');
  [['PARAMETERS',run.parameters.toLocaleString()],['INITIAL VALIDATION',run.history[0].validation_loss.toFixed(3)],['FINAL VALIDATION',run.history.at(-1).validation_loss.toFixed(3)]].forEach(([label,value])=>{const box=el('div',undefined,'baseline-metric');box.append(el('small',label),el('strong',value));metrics.append(box);});
  const summary=el('p',`${run.train_sentences.toLocaleString()} training sentences · ${run.validation_sentences.toLocaleString()} held-out sentences · ${run.vocabulary_size} vocabulary items · CPU · loss in nats per scored token.`,'baseline-summary');
  const replay=el('div',undefined,'baseline-replay');
  const label=el('label','Replay optimizer step: ');label.htmlFor='baseline-step';const step=el('strong','0');label.append(step);
  const slider=el('input');slider.type='range';slider.id='baseline-step';slider.min='0';slider.max=String(run.history.length-1);slider.step='1';slider.value='0';
  const reading=el('p');reading.setAttribute('aria-live','polite');
  const refs=el('p',`Uniform guessing: ${run.uniform_loss.toFixed(3)}. Training-word-frequency baseline: ${run.unigram_loss.toFixed(3)} on validation. These reference strategies do not read the context.`);
  const draw=()=>{const h=run.history[Number(slider.value)];step.textContent=String(h.step);reading.textContent=`Training loss: ${h.train_loss.toFixed(3)} · Validation loss: ${h.validation_loss.toFixed(3)}. Both are measured without updating the weights at this checkpoint.`;};
  slider.addEventListener('input',draw);draw();replay.append(label,slider,reading,refs);host.replaceChildren(metrics,summary,replay);
  const samples=document.getElementById('baseline-samples');
  run.samples.forEach(sample=>{const box=el('div',undefined,'baseline-sample');box.append(el('h4',`Prompt: ${sample.prompt}`),el('small','BEFORE TRAINING'),el('p',sample.before),el('small','AFTER TRAINING'),el('p',sample.after,'after'));samples.append(box);});
  document.getElementById('baseline-run-command').textContent=run.command;
 }).catch(error=>{host.replaceChildren(el('p',`${error.message}. The chart and downloadable run below remain available.`));});
})();

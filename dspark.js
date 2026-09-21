(()=>{
  'use strict';
  const root=document.getElementById('dspark'); if(!root)return;
  const inputs=[1,2,3,4,5].map(i=>root.querySelector(`#dspark-a${i}`));
  const body=root.querySelector('#dspark-table-body');
  const format=x=>Number(x).toFixed(2);
  function update(){
    const values=inputs.map((input,i)=>{const value=Number(input.value);root.querySelector(`#dspark-a${i+1}-value`).value=format(value);return value;});
    let survival=1, expected=0, best={length:1,score:-Infinity,survival:0,expected:0,cost:0}; body.replaceChildren();
    values.forEach((value,index)=>{
      survival*=value;
      expected+=survival;
      const cost=1+0.45*(index+1); // Explicitly invented arbitrary cost units for this teaching widget.
      const score=expected/cost;
      if(score>best.score)best={length:index+1,score,survival,expected,cost};
      const row=document.createElement('tr');
      row.innerHTML=`<td>1–${index+1}</td><td>${format(value)}</td><td>${format(survival)}</td><td>${format(expected)}</td><td>${format(cost)}</td><td>${format(score)}</td>`;
      row.dataset.length=String(index+1); body.append(row);
    });
    body.querySelector(`[data-length="${best.length}"]`).classList.add('is-choice');
    root.querySelector('#dspark-choice').textContent=`${best.length} position${best.length===1?'':'s'}`;
    root.querySelector('#dspark-expected').textContent=format(best.expected);
    root.querySelector('#dspark-score').textContent=format(best.score);
    root.querySelector('#dspark-explanation').textContent=`With these invented estimates, verifying through ${best.length} positions has expected accepted draft tokens E[A] = ${format(best.expected)} and invented cost C = ${format(best.cost)}, giving E[A]/C = ${format(best.score)}. The calculation excludes correction and bonus tokens. It is not DeepSeek’s profiled scheduler and does not predict real throughput.`;
  }
  inputs.forEach(input=>input.addEventListener('input',update)); update();
  root.querySelector('#dspark-run-toy').addEventListener('click',()=>{
    const draft=['is','ready','now','for','review'];
    const target=['is','ready','now','today','review'];
    let count=0; while(count<draft.length&&draft[count]===target[count])count++;
    root.querySelector('#dspark-draft-line').textContent=draft.join(' · ');
    root.querySelector('#dspark-verify-line').textContent=draft.map((word,i)=>i<count?'match':i===count?'reject':'—').join(' · ');
    root.querySelector('#dspark-accepted-line').textContent=count?draft.slice(0,count).join(' · '):'no proposed token committed';
    root.querySelector('#dspark-toy-result').textContent=`The fixed lists match for ${count} positions, so the illustration commits “${draft.slice(0,count).join(' ')}” and stops at “${draft[count]}”. Real speculative decoding must perform probability-aware acceptance and correction; this string comparison does not do that.`;
  });
})();

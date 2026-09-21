(()=>{
 const input=document.getElementById('fp4-input'),scale=document.getElementById('fp4-scale');if(!input)return;
 const levels=[-6,-4,-3,-2,-1.5,-1,-.5,0,.5,1,1.5,2,3,4,6];
 function draw(){
  const x=Number(input.value),s=Number(scale.value),values=levels.map(v=>v*s);
  const best=values.reduce((i,v,j)=>Math.abs(v-x)<Math.abs(values[i]-x)?j:i,0),y=values[best],error=y-x;
  document.getElementById('fp4-input-value').textContent=x.toFixed(2);
  document.getElementById('fp4-level').textContent=String(levels[best]);
  document.getElementById('fp4-reconstructed').textContent=y.toFixed(2);
  document.getElementById('fp4-error').textContent=(error>0?'+':'')+error.toFixed(2);
  const bound=Math.max(5,6*s),position=v=>(v+bound)/(2*bound)*100;
  document.getElementById('fp4-ticks').replaceChildren(...values.map((v,i)=>{const tick=document.createElement('i');tick.style.left=position(v)+'%';tick.title=String(v);if(i===best)tick.className='selected';return tick}));
  document.getElementById('fp4-original-marker').style.left=position(x)+'%';
  const clipped=Math.abs(x)>6*s;
  document.getElementById('fp4-demo-explanation').textContent=`${x.toFixed(2)} is stored as level ${levels[best]} with scale ${s}. Reading it gives ${levels[best]} × ${s} = ${y.toFixed(2)}. ${clipped?'The input exceeds this scale’s range, so it is clipped to an endpoint.':Math.abs(error)<1e-8?'This value is exactly representable at this scale.':'Rounding changed the value; reconstructing it cannot recover the missing detail.'}`;
 }
 input.addEventListener('input',draw);scale.addEventListener('change',draw);draw();
})();

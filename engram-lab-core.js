/* Tiny Engram mechanism lab. No dependencies, trained weights, or DeepSeek inference. */
(function(root){
 'use strict';
 const orders=[2,3,4], known={i:41,love:9,new:72,york:18,city:23};
 function seedValue(seed){let x=seed|0;x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967295*2-1;}
 function tokenId(word){const lower=word.toLowerCase();if(Object.hasOwn(known,lower))return known[lower];let h=2166136261;for(const c of lower)h=Math.imul(h^c.codePointAt(0),16777619);return 100+(h>>>0);}
 function tokenize(sentence){return sentence.trim().split(/\s+/u).filter(Boolean).slice(0,32).map(word=>({word,id:tokenId(word)}));}
 function groups(tokens,position){return orders.map(n=>({n,words:Array.from({length:n},(_,j)=>tokens[position-n+1+j]?.word??'PAD'),ids:Array.from({length:n},(_,j)=>tokens[position-n+1+j]?.id??0)}));}
 function hash(ids,head,rows){const base=31+2*head;return ids.reduce((acc,id)=>(base*acc+id)%rows,0);}
 const modelCache=new Map();
 function tables(heads,rows){const cacheKey=`${heads}:${rows}`;if(!modelCache.has(cacheKey))modelCache.set(cacheKey,orders.map(n=>Array.from({length:heads},(_,h)=>Array.from({length:rows},(_,r)=>Array.from({length:3},(_,d)=>seedValue(Math.imul(n*1000003+h*1009+r*17+d+1,2654435761)))))));return modelCache.get(cacheKey);}
 function lookup(ids,heads=8,rows=101){const table=tables(heads,rows)[ids.length-2];return Array.from({length:heads},(_,head)=>{const row=hash(ids,head,rows);return {head,row,vector:table[head][row].slice()};});}
 function project(values,seed){return Array.from({length:3},(_,d)=>values.reduce((s,x,j)=>s+x*seedValue(Math.imul(seed+j*31+d*1009,2246822519)),0)/Math.sqrt(values.length));}
 function retrieve(tokenGroups,heads,rows){const lookups=tokenGroups.map(g=>({...g,lookups:lookup(g.ids,heads,rows)}));const flat=lookups.flatMap(g=>g.lookups.flatMap(h=>h.vector));return {groups:lookups,key:project(flat,719),value:project(flat,1237)};}
 function unit(v){const norm=Math.hypot(...v);return norm>1e-10?v.map(x=>x/norm):[1,0,0];}
 function contextGate(key,value,degrees){const k=unit(key),ref=Math.abs(k[0])<.9?[1,0,0]:[0,1,0];const dot=k.reduce((s,x,j)=>s+x*ref[j],0),perp=unit(ref.map((x,j)=>x-dot*k[j]));const theta=degrees*Math.PI/180;const hidden=k.map((x,j)=>Math.cos(theta)*x+Math.sin(theta)*perp[j]);const cosine=hidden.reduce((s,x,j)=>s+x*k[j],0);const gate=1/(1+Math.exp(-3*cosine));const added=value.map(x=>gate*x);return {hidden,cosine,gate,added,output:hidden.map((x,j)=>x+added[j])};}
 function signature(ids,heads,rows){return Array.from({length:heads},(_,h)=>hash(ids,h,rows));}
 function collisionExperiment(rows){const inputs=[];for(let a=1;a<=16;a++)for(let b=1;b<=16;b++)inputs.push([a,b]);
  function measure(heads){const buckets=new Map();for(const pair of inputs){const sig=signature(pair,heads,rows).join(',');if(!buckets.has(sig))buckets.set(sig,[]);buckets.get(sig).push(pair);}return {heads,distinct:buckets.size,sharedGroups:[...buckets.values()].reduce((s,b)=>s+(b.length>1?b.length:0),0),buckets};}
  const one=measure(1),eight=measure(8);let example=null;
  outer:for(const bucket of one.buckets.values())if(bucket.length>1){for(let i=0;i<bucket.length;i++)for(let j=i+1;j<bucket.length;j++){const a=bucket[i],b=bucket[j];if(!example)example=[a,b];if(signature(a,8,rows).join()!=signature(b,8,rows).join()){example=[a,b];break outer;}}}
  if(eight.sharedGroups){const fullCollision=[...eight.buckets.values()].find(bucket=>bucket.length>1);example=fullCollision.slice(0,2);}
  return {total:inputs.length,rows,one:{heads:1,distinct:one.distinct,sharedGroups:one.sharedGroups},eight:{heads:8,distinct:eight.distinct,sharedGroups:eight.sharedGroups},example,addresses:example.map(p=>signature(p,8,rows))};
 }
 const api={orders,tokenize,groups,hash,lookup,retrieve,contextGate,collisionExperiment,signature};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ToyEngram=api;
})(typeof globalThis!=='undefined'?globalThis:this);

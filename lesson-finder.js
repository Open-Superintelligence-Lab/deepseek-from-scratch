(()=>{
 const input=document.getElementById('lesson-search');if(!input)return;
 const links=[...document.querySelectorAll('body > aside nav a')],status=document.getElementById('lesson-search-status');
 input.addEventListener('input',()=>{
  const words=input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);let count=0;
  links.forEach(link=>{const haystack=(link.textContent+' '+link.hash.replaceAll('-',' ')).toLowerCase();const visible=words.every(word=>haystack.includes(word));link.hidden=!visible;if(visible)count++});
  status.hidden=words.length===0;status.textContent=count?`${count} matching lesson${count===1?'':'s'}`:'No match. Try “cache”, “routing”, or “training”.';
 });
})();

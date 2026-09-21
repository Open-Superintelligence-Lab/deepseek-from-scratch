// Start still. Stop animation when it leaves view or the page is hidden.
(()=>{
 const buttons=[...document.querySelectorAll('.meme-toggle')];
 function setPlaying(button,play){
  const image=button.parentElement.querySelector('img');if(!image)return;
  image.src=play?image.dataset.memeGif:image.dataset.memeStill;
  button.setAttribute('aria-pressed',String(play));button.textContent=play?'Pause meme':'Play meme';
 }
 buttons.forEach(button=>button.addEventListener('click',()=>setPlaying(button,button.getAttribute('aria-pressed')!=='true')));
 if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
   if(!entry.isIntersecting){const button=entry.target.querySelector('.meme-toggle');if(button?.getAttribute('aria-pressed')==='true')setPlaying(button,false)}
  }));buttons.forEach(button=>observer.observe(button.closest('.course-meme')));
 }
 document.addEventListener('visibilitychange',()=>{if(document.hidden)buttons.forEach(button=>{if(button.getAttribute('aria-pressed')==='true')setPlaying(button,false)})});
})();

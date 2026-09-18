/* =========================================================
   homepage.js
   PRUEBA: transición noche → día del hero, ligada al scroll.
   El hero se pinea mientras dura la transición; la imagen de
   día sube de opacidad 0 → 1 de forma smooth (scrub) a medida
   que el usuario baja el scroll, y vuelve a noche si sube.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  const hero = document.getElementById('hero');
  const dia = hero ? hero.querySelector('.hero-bg--dia') : null;
  if (!hero || !dia) return;

  gsap.timeline({
    scrollTrigger: {
      trigger: hero,
      start: 'top top',
      end: '+=100%',
      scrub: true,
      pin: true,
      anticipatePin: 1
    }
  }).to(dia, {
    opacity: 1,
    ease: 'none'
  });
});

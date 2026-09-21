/* =========================================================
   homepage.js
   PRUEBA: transicion noche -> dia del hero, ligada al scroll.
   El hero se pinea mientras dura la transicion; la imagen de
   dia sube de opacidad 0 -> 1 de forma smooth (scrub) a medida
   que el usuario baja el scroll, y vuelve a noche si sube.

   En mobile, ademas, el texto del hero sube en sincronia con ese
   mismo scroll pineado: como el fondo solo (cambiando de opacidad
   despacio) no transmite que se sigue scrolleando, sin este
   movimiento la pantalla se siente "trabada" al bajar.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  const hero = document.getElementById('hero');
  const dia = hero ? hero.querySelector('.hero-bg--dia') : null;
  const heroText = hero ? hero.querySelector('.hero-text') : null;
  if (!hero || !dia) return;

  const mm = gsap.matchMedia();

  mm.add('(max-width: 768px)', function () {
    const tl = gsap.timeline({
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
    }, 0);

    if (heroText) {
      tl.to(heroText, {
        y: -120,
        ease: 'none'
      }, 0);
    }
  });

  mm.add('(min-width: 769px)', function () {
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
});

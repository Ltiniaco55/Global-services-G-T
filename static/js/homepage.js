/* =========================================================
   homepage.js
   Transicion noche -> dia del hero, ligada al scroll (pin corto).
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
  const fondos = hero.querySelectorAll('.hero-bg');

  // Pin más corto (media pantalla de scroll en vez de una entera) y con
  // scrub suavizado, para que no se sienta "trabado". Mientras dura, la
  // foto pasa de noche a día y se aleja un poco (zoom leve) para que se
  // note que el scroll sigue avanzando.
  const PIN = {
    trigger: hero,
    start: 'top top',
    end: '+=50%',
    scrub: 0.6,
    pin: true,
    anticipatePin: 1
  };

  mm.add('(max-width: 768px)', function () {
    const tl = gsap.timeline({ scrollTrigger: PIN })
      .to(dia, { opacity: 1, ease: 'none' }, 0)
      .fromTo(fondos, { scale: 1.08 }, { scale: 1, ease: 'none' }, 0);

    if (heroText) {
      tl.to(heroText, { y: -60, ease: 'none' }, 0);
    }
  });

  mm.add('(min-width: 769px)', function () {
    gsap.timeline({ scrollTrigger: PIN })
      .to(dia, { opacity: 1, ease: 'none' }, 0)
      .fromTo(fondos, { scale: 1.08 }, { scale: 1, ease: 'none' }, 0);
  });
});

/* =========================================================
   Carrusel de fotos del hero (tarjeta de cristal) y contador
   animado de las cifras. No dependen de GSAP.
   ========================================================= */
document.addEventListener('DOMContentLoaded', function () {
  const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // --- Carrusel: cambia de foto cada `data-intervalo` ms; se pausa con
  //     el mouse encima; clic en la tarjeta = siguiente foto.
  const carrusel = document.querySelector('[data-carrusel]');
  if (carrusel) {
    const fotos = carrusel.querySelectorAll('.hero-carrusel__foto');
    const barras = carrusel.querySelectorAll('.hero-carrusel__barra');
    const actual = carrusel.querySelector('[data-carrusel-actual]');
    const total = carrusel.querySelector('[data-carrusel-total]');
    const intervalo = parseInt(carrusel.dataset.intervalo, 10) || 4500;
    const dosCifras = (n) => String(n).padStart(2, '0');
    let indice = 0;
    let timer = null;
    let restante = intervalo;
    let inicio = 0;

    carrusel.style.setProperty('--carrusel-intervalo', intervalo + 'ms');
    if (total) total.textContent = dosCifras(fotos.length);

    function mostrar(i) {
      indice = (i + fotos.length) % fotos.length;
      fotos.forEach((f, n) => f.classList.toggle('is-activa', n === indice));
      barras.forEach((b, n) => {
        b.classList.toggle('is-vista', n < indice);
        b.classList.remove('is-activa');
      });
      // reflow para reiniciar la animación de la barra
      void carrusel.offsetWidth;
      if (barras[indice]) barras[indice].classList.add('is-activa');
      if (actual) actual.textContent = dosCifras(indice + 1);
      programar(intervalo);
    }

    function programar(ms) {
      clearTimeout(timer);
      restante = ms;
      inicio = Date.now();
      timer = setTimeout(() => mostrar(indice + 1), ms);
    }

    if (fotos.length > 1 && !reducirMovimiento) {
      programar(intervalo);
      carrusel.addEventListener('mouseenter', () => {
        clearTimeout(timer);
        restante -= Date.now() - inicio;
      });
      carrusel.addEventListener('mouseleave', () => programar(Math.max(restante, 300)));
      carrusel.addEventListener('click', () => mostrar(indice + 1));
      carrusel.style.cursor = 'pointer';
    }
  }

  // --- Cifras: cuentan de 0 al valor final al cargar. El número real ya
  //     está en el HTML (SEO / sin JavaScript); esto es solo el efecto.
  if (!reducirMovimiento) {
    document.querySelectorAll('[data-contador]').forEach((el) => {
      const final = parseInt(el.dataset.contador, 10);
      if (!final) return;
      const duracion = 1600;
      const t0 = performance.now();
      function paso(t) {
        const p = Math.min((t - t0) / duracion, 1);
        const suave = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(final * suave);
        if (p < 1) requestAnimationFrame(paso);
      }
      el.textContent = '0';
      requestAnimationFrame(paso);
    });
  }
});

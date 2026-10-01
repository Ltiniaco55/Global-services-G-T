/* =========================================================
   animaciones.js — efectos de scroll en TODO el sitio
   (se carga en base.html después de GSAP, ScrollTrigger y Lenis)

   1. Scroll suave con inercia (Lenis) — solo con rueda/trackpad;
      en móvil se deja el scroll táctil nativo del teléfono.
   2. Barra de progreso de lectura (línea lima arriba).
   3. Aparición de secciones: títulos, textos y tarjetas entran con un
      fundido + subida corta, en cascada cuando van en grupo.
   4. Parallax sutil: el contenido de los heroes internos y los bloques
      de imagen se mueven un poco distinto al resto al hacer scroll.

   El header inteligente (se esconde al bajar, vuelve al subir) está en
   layout.js. El hero de la home (pin noche → día) está en homepage.js.

   Accesibilidad: si el usuario tiene activado "reducir movimiento" en su
   sistema, no se aplica nada de esto y la página funciona como siempre.
   Si GSAP/Lenis no cargan (sin internet, bloqueador), el contenido se ve
   normal: los estados iniciales ocultos los pone este mismo script.
   ========================================================= */
(function () {
  const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducirMovimiento || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  // --- 1. Scroll suave (Lenis) sincronizado con ScrollTrigger -----------
  let lenis = null;
  if (typeof Lenis !== 'undefined') {
    lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });
    window.lenis = lenis; // para que otros scripts puedan pausarlo
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);

    // Enlaces internos (#servicios, #quienes-somos...) con el mismo scroll
    // suave, dejando sitio para el header fijo.
    document.addEventListener('click', (evento) => {
      const enlace = evento.target.closest('a[href*="#"]');
      if (!enlace) return;
      const url = new URL(enlace.href, window.location.href);
      if (url.pathname !== window.location.pathname || !url.hash) return;
      const destino = document.getElementById(decodeURIComponent(url.hash.slice(1)));
      if (!destino) return;
      evento.preventDefault();
      lenis.scrollTo(destino, { offset: -90 });
      history.pushState(null, '', url.hash);
    });
  }

  // --- 2. Barra de progreso -------------------------------------------
  const barra = document.querySelector('.barra-progreso');
  if (barra) {
    gsap.to(barra, {
      scaleX: 1,
      ease: 'none',
      scrollTrigger: { start: 0, end: 'max', scrub: 0.3 },
    });
  }

  // --- 3 y 4. Se montan después de que homepage.js cree el pin del hero,
  //     para que las posiciones de todo lo de abajo se calculen bien.
  document.addEventListener('DOMContentLoaded', () => requestAnimationFrame(montarEfectos));

  function montarEfectos() {
    // Elementos que aparecen al entrar en pantalla. Se excluye lo que está
    // dentro del hero de la home (tiene su propia animación).
    const SELECTORES = [
      '.section-tag', '.section-title', '.section-lead', '.section-note',
      '.page-hero .container > *', '.detalle-hero .container > *',
      '.detalle-intro', '.detalle-subtitle', '.detalle-img',
      '.mv-card', '.pill-card', '.logo-slot', '.servicio-card',
      '.seguridad-item', '.seguridad-badges', '.proyecto-img', '.proyecto-caption',
      '.faq-item', '.trabajo-cta', '.cta-final__inner > *',
      '.flota-card', '.relacionado-card', '.detalle-incluye-item',
      '.proceso-card', '.specs-box', '.quote-cta', '.cta-cotizacion',
      '.cotizacion-card', '.proyecto-row', '.footer-grid > div', '.footer-copy',
      // versión con fotos (fotos.css)
      '.foto-card', '.historia__fotos', '.historia__texto > *', '.antes-despues',
      '.destacado__texto > *', '.confianza__bloque', '.confianza__certs li', '.base-card',
      '.base-fila', '.embarcacion', '.galeria__item', '.chips', '.foto-unica', '.filtros',
    ].join(',');

    // Fuera lo que está en el hero de la home y lo que ya está dentro de
    // otro elemento animado (para no sumar dos fundidos uno encima de otro).
    const candidatos = gsap.utils.toArray(SELECTORES).filter((el) => !el.closest('#hero'));
    const elementos = candidatos.filter((el) => !candidatos.some((otro) => otro !== el && otro.contains(el)));
    if (elementos.length) {
      gsap.set(elementos, { autoAlpha: 0, y: 28 });
      ScrollTrigger.batch(elementos, {
        start: 'top 90%',
        // Se repite cada vez que bajas: al entrar aparece; si subes y el
        // elemento vuelve a quedar por debajo de la pantalla, se "rearma"
        // (vuelve a oculto) para aparecer otra vez en el siguiente paso.
        onEnter: (lote) => gsap.to(lote, {
          autoAlpha: 1,
          y: 0,
          duration: 0.8,
          ease: 'power3.out',
          stagger: 0.08,
          overwrite: true,
        }),
        onLeaveBack: (lote) => gsap.to(lote, {
          autoAlpha: 0,
          y: 28,
          duration: 0.3,
          overwrite: true,
        }),
      });

      // Red de seguridad: lo último de la página (ej. el copyright del
      // footer) puede no llegar nunca al 90% de la pantalla; al tocar el
      // final del scroll se muestra todo lo que quede pendiente.
      ScrollTrigger.create({
        start: () => ScrollTrigger.maxScroll(window) - 2,
        onEnter: () => gsap.to(elementos.filter((el) => el.style.visibility === 'hidden'), {
          autoAlpha: 1, y: 0, duration: 0.6, ease: 'power3.out', stagger: 0.05,
        }),
      });
    }

    // Parallax sutil en el contenido de los heroes internos: se queda un
    // poco atrás y se desvanece a medida que la página sube.
    gsap.utils.toArray('.page-hero .container, .detalle-hero .container').forEach((el) => {
      gsap.to(el, {
        yPercent: 18,
        opacity: 0.35,
        ease: 'none',
        scrollTrigger: { trigger: el.parentElement, start: 'top top', end: 'bottom top', scrub: true },
      });
    });

    // Parallax en fotos: cualquier imagen con el atributo data-parallax se
    // desplaza un poco más lento que la página. Uso: <img data-parallax>
    // dentro de un contenedor con overflow: hidden (la imagen algo más alta
    // que el contenedor). Valor opcional = intensidad, ej. data-parallax="15".
    gsap.utils.toArray('[data-parallax]').forEach((el) => {
      const intensidad = parseFloat(el.dataset.parallax) || 10;
      gsap.fromTo(el, { yPercent: -intensidad }, {
        yPercent: intensidad,
        ease: 'none',
        scrollTrigger: { trigger: el.parentElement, start: 'top bottom', end: 'bottom top', scrub: true },
      });
    });

    ScrollTrigger.refresh();
  }
})();

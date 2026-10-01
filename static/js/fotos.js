/* =========================================================
   fotos.js — interacción de las fotos:
   1. Comparador antes / después ([data-antes-despues])
   2. Visor a pantalla completa para enlaces con [data-visor]
      (las fotos con el mismo valor forman un grupo navegable)
   3. Filtro de proyectos por servicio ([data-filtros])
   ========================================================= */
(function () {
  'use strict';

  const EN = (document.documentElement.lang || '').startsWith('en');
  const T = EN
    ? { cerrar: 'Close', ant: 'Previous photo', sig: 'Next photo' }
    : { cerrar: 'Cerrar', ant: 'Foto anterior', sig: 'Foto siguiente' };

  // --- 1. Antes / después -------------------------------------------
  document.querySelectorAll('[data-antes-despues]').forEach((fig) => {
    const control = fig.querySelector('.antes-despues__control');
    if (!control) return;
    const aplicar = () => fig.style.setProperty('--pos', control.value + '%');
    control.addEventListener('input', aplicar);
    aplicar();
  });

  // --- 2. Visor --------------------------------------------------------
  const enlaces = Array.from(document.querySelectorAll('[data-visor]'));
  if (enlaces.length) {
    const visor = document.createElement('div');
    visor.className = 'visor';
    visor.setAttribute('role', 'dialog');
    visor.setAttribute('aria-modal', 'true');
    visor.innerHTML =
      '<img class="visor__img" alt="">' +
      '<p class="visor__titulo"></p>' +
      `<button type="button" class="visor__btn visor__btn--cerrar" aria-label="${T.cerrar}"><i class="ti ti-x"></i></button>` +
      `<button type="button" class="visor__btn visor__btn--ant" aria-label="${T.ant}"><i class="ti ti-chevron-left"></i></button>` +
      `<button type="button" class="visor__btn visor__btn--sig" aria-label="${T.sig}"><i class="ti ti-chevron-right"></i></button>`;
    document.body.appendChild(visor);

    const img = visor.querySelector('.visor__img');
    const titulo = visor.querySelector('.visor__titulo');
    const btnAnt = visor.querySelector('.visor__btn--ant');
    const btnSig = visor.querySelector('.visor__btn--sig');
    let grupo = [];
    let indice = 0;
    let origen = null;

    function mostrar(i) {
      indice = (i + grupo.length) % grupo.length;
      const a = grupo[indice];
      img.src = a.getAttribute('href');
      img.alt = a.dataset.titulo || '';
      titulo.textContent = a.dataset.titulo || '';
      const varias = grupo.length > 1;
      btnAnt.hidden = !varias;
      btnSig.hidden = !varias;
    }

    function abrir(a) {
      origen = a;
      grupo = enlaces.filter((e) => e.dataset.visor === a.dataset.visor);
      visor.classList.add('is-abierto');
      document.body.style.overflow = 'hidden';
      if (window.lenis) window.lenis.stop();
      mostrar(grupo.indexOf(a));
      visor.querySelector('.visor__btn--cerrar').focus();
    }

    function cerrar() {
      visor.classList.remove('is-abierto');
      document.body.style.overflow = '';
      if (window.lenis) window.lenis.start();
      if (origen) origen.focus();
    }

    enlaces.forEach((a) => a.addEventListener('click', (e) => {
      e.preventDefault();
      abrir(a);
    }));
    visor.querySelector('.visor__btn--cerrar').addEventListener('click', cerrar);
    btnAnt.addEventListener('click', () => mostrar(indice - 1));
    btnSig.addEventListener('click', () => mostrar(indice + 1));
    visor.addEventListener('click', (e) => { if (e.target === visor) cerrar(); });
    document.addEventListener('keydown', (e) => {
      if (!visor.classList.contains('is-abierto')) return;
      if (e.key === 'Escape') cerrar();
      if (e.key === 'ArrowLeft') mostrar(indice - 1);
      if (e.key === 'ArrowRight') mostrar(indice + 1);
    });

    // Deslizar con el dedo en móvil
    let x0 = null;
    visor.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
    visor.addEventListener('touchend', (e) => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50 && grupo.length > 1) mostrar(indice + (dx < 0 ? 1 : -1));
      x0 = null;
    });
  }

  // --- 3. Filtro de proyectos -----------------------------------------
  const filtros = document.querySelector('[data-filtros]');
  const rejilla = document.querySelector('[data-filtrable]');
  if (filtros && rejilla) {
    filtros.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-filtro]');
      if (!btn) return;
      const valor = btn.dataset.filtro;
      filtros.querySelectorAll('[data-filtro]').forEach((b) => b.classList.toggle('is-activo', b === btn));
      rejilla.querySelectorAll('.foto-card').forEach((card) => {
        const ver = !valor || card.dataset.servicio === valor;
        card.classList.toggle('is-oculta', !ver);
        // las tarjetas ya ocultas por la animación de entrada se muestran
        if (ver && window.gsap) window.gsap.set(card, { autoAlpha: 1, y: 0 });
      });
      if (window.ScrollTrigger) window.ScrollTrigger.refresh();
    });
  }
})();

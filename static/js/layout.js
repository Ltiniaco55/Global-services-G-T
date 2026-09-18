/* =========================================================
   layout.js (adaptado para Django)

   En la versión estática original este archivo inyectaba header,
   footer, burger y la card de cotización vía fetch() en tiempo de
   ejecución. En Django esos mismos partials se renderizan del lado
   del servidor con {% include %} (ver templates/includes/ y base.html),
   así que la parte de fetch/injectLayout ya no hace falta y se quitó
   para no duplicar contenido ni disparar peticiones innecesarias.

   El comportamiento JS real de la página (dim del header al hacer
   scroll, abrir/cerrar el menú burger, encoger el botón flotante de
   WhatsApp, el globo de mensaje de WhatsApp) se mantiene exactamente
   igual que en el original.
   ========================================================= */

function initHeaderScrollBehavior() {
  const header = document.querySelector('.site-header');
  if (!header) return;
  let lastY = window.scrollY;
  window.addEventListener('scroll', () => {
    const currentY = window.scrollY;
    if (currentY > lastY && currentY > 80) {
      header.classList.add('header--dim');
    } else {
      header.classList.remove('header--dim');
    }
    lastY = currentY;
  });
}

function initBurgerMenu() {
  const toggle = document.querySelector('.burger-toggle');
  const panel = document.querySelector('.burger-panel');
  const closeBtn = document.querySelector('.burger-close');
  if (!toggle || !panel) return;

  function setOpen(isOpen) {
    panel.classList.toggle('burger-panel--open', isOpen);
    const icon = toggle.querySelector('i');
    if (icon) icon.className = isOpen ? 'ti ti-x' : 'ti ti-menu-2';
  }

  toggle.addEventListener('click', () => {
    setOpen(!panel.classList.contains('burger-panel--open'));
  });
  closeBtn?.addEventListener('click', () => setOpen(false));

  // cerrar al hacer click en un link del menú
  panel.querySelectorAll('a').forEach((a) =>
    a.addEventListener('click', () => setOpen(false))
  );
}

function initWhatsappFloatBehavior() {
  const btn = document.querySelector('.whatsapp-float');
  if (!btn) return;
  let lastY = window.scrollY;
  window.addEventListener('scroll', () => {
    const currentY = window.scrollY;
    btn.classList.toggle('whatsapp-float--small', currentY > lastY);
    lastY = currentY;
  });
}

function initWhatsappBubble() {
  const btn = document.querySelector('.whatsapp-float');
  const bubble = document.querySelector('.whatsapp-bubble');
  if (!btn || !bubble) return;

  let hideTimer = null;
  let hovering = false;

  function showBubble() {
    clearTimeout(hideTimer);
    bubble.classList.add('whatsapp-bubble--visible');
  }

  function hideBubble() {
    bubble.classList.remove('whatsapp-bubble--visible');
  }

  function scheduleHide(delay) {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => {
      if (!hovering) hideBubble();
    }, delay);
  }

  // Se muestra sola al entrar a la página, durante 5 segundos.
  showBubble();
  scheduleHide(5000);

  // Además, aparece cada vez que se pasa el mouse por encima del
  // botón (o del propio globo, para poder acercarse sin que se
  // esconda de golpe).
  [btn, bubble].forEach((el) => {
    el.addEventListener('mouseenter', () => {
      hovering = true;
      showBubble();
    });
    el.addEventListener('mouseleave', () => {
      hovering = false;
      scheduleHide(300);
    });
  });

  const closeBtn = bubble.querySelector('.whatsapp-bubble__close');
  closeBtn?.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    hovering = false;
    hideBubble();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initHeaderScrollBehavior();
  initBurgerMenu();
  initWhatsappFloatBehavior();
  initWhatsappBubble();

  // Se mantiene el evento para que el JS propio de cada página (ej. el
  // ScrollTrigger del hero en homepage.js) pueda seguir escuchándolo si
  // lo necesita, aunque ahora el header/footer ya están en el DOM desde
  // el primer render (no hay que esperar un fetch).
  document.dispatchEvent(new CustomEvent('layouts:ready'));
});

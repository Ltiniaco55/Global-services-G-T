/**
 * Selector de teléfono con código de país (intl-tel-input) + validación de
 * campos obligatorios antes de enviar los formularios de /contacto/ y
 * /cotizacion/. Un mismo helper para ambas páginas: cada una solo indica,
 * vía `opciones`, qué campos aplican (por ejemplo /contacto/ no tiene
 * "asunto" ni checkboxes de servicios).
 *
 * Esto es una capa de comodidad para el usuario (mensajes en español, en
 * el estilo del sitio, sin recargar la página). La validación real e
 * inquebrantable vive en sitio/forms.py — si JavaScript falla o está
 * desactivado, el formulario igual no se puede enviar incompleto porque
 * Django lo vuelve a validar del lado del servidor.
 */
function initFormValidado(form, opciones) {
  if (!form) return;

  var cfg = Object.assign({
    telefonoInputId: null,
    paisInicial: 've',
    asuntoInputName: null,
    asuntoMinPalabras: 3,
    asuntoMaxPalabras: 12,
    checkboxGrupoSelector: null,
    checkboxGrupoErrorMsg: 'Selecciona al menos una opción.',
    archivoRequeridoId: null,
    archivoRequeridoMsg: 'Adjunta un archivo.',
  }, opciones || {});

  var iti = null;
  var telInput = cfg.telefonoInputId ? document.getElementById(cfg.telefonoInputId) : null;

  if (telInput && window.intlTelInput) {
    iti = window.intlTelInput(telInput, {
      initialCountry: cfg.paisInicial,
      preferredCountries: ['ve', 'co', 'us', 'es'],
      separateDialCode: true,
      utilsScript: 'https://cdn.jsdelivr.net/npm/intl-tel-input@18.5.3/build/js/utils.js',
    });
  }

  function limpiarError(clave) {
    form.querySelectorAll('[data-error-de="' + clave + '"]').forEach(function (el) {
      el.remove();
    });
  }

  function mostrarError(clave, despuesDe, mensaje) {
    limpiarError(clave);
    var p = document.createElement('p');
    p.className = 'form-error';
    p.setAttribute('data-error-de', clave);
    p.textContent = mensaje;
    despuesDe.insertAdjacentElement('afterend', p);
  }

  function contarPalabras(texto) {
    return texto.trim().split(/\s+/).filter(Boolean).length;
  }

  form.addEventListener('submit', function (evento) {
    var valido = true;
    var primerInvalido = null;

    function marcarInvalido(campo, clave, mensaje, despuesDe) {
      valido = false;
      mostrarError(clave, despuesDe || campo, mensaje);
      if (!primerInvalido) primerInvalido = campo;
    }

    // Nombre y apellido
    var nombre = form.querySelector('[name="nombre"]');
    if (nombre) {
      limpiarError('nombre');
      if (!nombre.value.trim()) {
        marcarInvalido(nombre, 'nombre', 'Ingresa tu nombre y apellido.');
      }
    }

    // Correo
    var email = form.querySelector('[name="email"]');
    if (email) {
      limpiarError('email');
      var regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!email.value.trim() || !regexEmail.test(email.value.trim())) {
        marcarInvalido(email, 'email', 'Ingresa un correo válido.');
      }
    }

    // Teléfono (usa la validación real del país seleccionado si el
    // selector cargó bien; si no, al menos exige un número no vacío)
    if (telInput) {
      limpiarError('telefono');
      var contenedorTel = telInput.closest('.iti') || telInput;
      var telVacio = !telInput.value.trim();
      var telValido = iti ? iti.isValidNumber() : telInput.value.trim().length >= 7;
      if (telVacio || !telValido) {
        marcarInvalido(telInput, 'telefono', 'Ingresa un número de teléfono válido.', contenedorTel);
      } else if (iti) {
        telInput.value = iti.getNumber();
      }
    }

    // Asunto (solo en /cotizacion/)
    if (cfg.asuntoInputName) {
      var asunto = form.querySelector('[name="' + cfg.asuntoInputName + '"]');
      if (asunto) {
        limpiarError('asunto');
        var valorAsunto = asunto.value.trim();
        if (!valorAsunto) {
          marcarInvalido(asunto, 'asunto', 'Escribe el asunto de tu solicitud.');
        } else {
          var palabras = contarPalabras(valorAsunto);
          if (palabras < cfg.asuntoMinPalabras || palabras > cfg.asuntoMaxPalabras) {
            marcarInvalido(
              asunto,
              'asunto',
              'El asunto debe tener entre ' + cfg.asuntoMinPalabras + ' y ' + cfg.asuntoMaxPalabras + ' palabras.'
            );
          }
        }
      }
    }

    // Al menos un checkbox de servicios (solo en /cotizacion/)
    if (cfg.checkboxGrupoSelector) {
      var grupo = form.querySelector(cfg.checkboxGrupoSelector);
      if (grupo) {
        limpiarError('servicios');
        var marcado = grupo.querySelector('input[type="checkbox"]:checked');
        if (!marcado) {
          valido = false;
          mostrarError('servicios', grupo, cfg.checkboxGrupoErrorMsg);
          if (!primerInvalido) primerInvalido = grupo.querySelector('input[type="checkbox"]');
        }
      }
    }

    // Archivo obligatorio (por ejemplo, el currículum en "Trabaja con
    // Nosotros"): al menos un archivo seleccionado.
    if (cfg.archivoRequeridoId) {
      var archivoInput = document.getElementById(cfg.archivoRequeridoId);
      if (archivoInput) {
        limpiarError('archivo');
        if (!archivoInput.files || archivoInput.files.length === 0) {
          marcarInvalido(
            archivoInput,
            'archivo',
            cfg.archivoRequeridoMsg,
            archivoInput.closest('div') || archivoInput
          );
        }
      }
    }

    // Aceptación de la política de privacidad (solo en /cotizacion/)
    var privacidad = form.querySelector('[name="acepta_privacidad"]');
    if (privacidad) {
      limpiarError('acepta_privacidad');
      if (!privacidad.checked) {
        var etiquetaPrivacidad = privacidad.closest('.privacy-check') || privacidad;
        marcarInvalido(
          privacidad,
          'acepta_privacidad',
          'Debes aceptar la política de privacidad para continuar.',
          etiquetaPrivacidad
        );
      }
    }

    if (!valido) {
      evento.preventDefault();
      if (primerInvalido && primerInvalido.focus) primerInvalido.focus();
    }
  });
}

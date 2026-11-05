(function () {
  function bloquear(btn) {
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.dataset.bloqueadoPorClic = "1";
    btn.style.opacity = "0.6";
    btn.style.cursor = "not-allowed";
  }

  function liberar(btn) {
    if (!btn || btn.dataset.bloqueadoPorClic !== "1") return;
    btn.disabled = false;
    delete btn.dataset.bloqueadoPorClic;
    btn.style.opacity = "";
    btn.style.cursor = "";
  }

  var SELECTOR = 'button[type="submit"], button:not([type]), input[type="submit"]';

  function botonesDe(el) {
    if (!el) return [];
    if (el.matches && el.matches("button, input[type=submit]")) return [el];
    if (el.querySelectorAll) return Array.prototype.slice.call(el.querySelectorAll(SELECTOR));
    return [];
  }

  // Formularios normales: se bloquea después de que el navegador toma los datos.
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (form.hasAttribute("data-sin-bloqueo")) return;
    var botones = botonesDe(form);
    setTimeout(function () {
      if (e.defaultPrevented) return; // validación o confirmación cancelada
      botones.forEach(bloquear);
    }, 0);
  });

  // Botones con htmx (aceptar/rechazar en /gestion/): bloqueados mientras dura la petición.
  document.addEventListener("htmx:beforeRequest", function (e) {
    botonesDe(e.detail.elt).forEach(bloquear);
  });
  document.addEventListener("htmx:afterRequest", function (e) {
    botonesDe(e.detail.elt).forEach(liberar);
  });

  // Si el usuario vuelve con el botón "atrás", no deja la página bloqueada.
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) {
      document.querySelectorAll('[data-bloqueado-por-clic="1"]').forEach(liberar);
    }
  });
})();
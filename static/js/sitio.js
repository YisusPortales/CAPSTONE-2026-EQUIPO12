(function () {
  "use strict";

  // ---- Paneles laterales (se abren de derecha a izquierda) ----
  const fondo = document.getElementById("panel-fondo");
  let panelAbierto = null;
  let botonOrigen = null;

  function abrirPanel(id, boton) {
    const panel = document.getElementById(id);
    if (!panel) return;
    panelAbierto = panel;
    botonOrigen = boton;
    fondo.classList.remove("hidden");
    panel.inert = false;
    panel.setAttribute("aria-hidden", "false");
    panel.classList.remove("translate-x-full");
    document.body.classList.add("overflow-hidden");
    const cerrar = panel.querySelector("[data-cerrar]");
    if (cerrar) cerrar.focus();
  }

  function cerrarPanel() {
    if (!panelAbierto) return;
    panelAbierto.classList.add("translate-x-full");
    panelAbierto.setAttribute("aria-hidden", "true");
    panelAbierto.inert = true;
    fondo.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    if (botonOrigen) botonOrigen.focus();
    panelAbierto = null;
    botonOrigen = null;
  }

  document.addEventListener("click", function (evento) {
    const boton = evento.target.closest("[data-panel]");
    if (boton) {
      abrirPanel(boton.dataset.panel, boton);
      return;
    }
    if (evento.target.closest("[data-cerrar]")) cerrarPanel();
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && panelAbierto) cerrarPanel();
  });

  // ---- Formulario: mostrar las habitaciones solo si eligen "Habitaciones específicas" ----
  const alojamiento = document.getElementById("id_alojamiento");
  const bloqueHabitaciones = document.getElementById("bloque-habitaciones");

  function actualizarHabitaciones() {
    if (!alojamiento || !bloqueHabitaciones) return;
    bloqueHabitaciones.hidden = alojamiento.value !== "habitaciones";
  }

  if (alojamiento) {
    alojamiento.addEventListener("change", actualizarHabitaciones);
    actualizarHabitaciones();
  }

   // ---- Menús desplegables de la cabecera: cerrar al hacer clic fuera o con Escape ----
  document.addEventListener("click", function (evento) {
    document.querySelectorAll("header details[open]").forEach(function (menu) {
      if (!menu.contains(evento.target)) menu.removeAttribute("open");
    });
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key !== "Escape") return;
    document.querySelectorAll("header details[open]").forEach(function (menu) {
      menu.removeAttribute("open");
      const resumen = menu.querySelector("summary");
      if (resumen) resumen.focus();
    });
  });

  document.addEventListener("click", function (ev) {
  var enlace = ev.target.closest("[data-ir-arriba]");
  if (!enlace) return;
  if (window.location.pathname === enlace.pathname) {
    ev.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
    history.replaceState(null, "", enlace.pathname);
  }
  });

    // ---- Menú: marca la sección que se está viendo ----
  (function () {
    const enlaces = [];
    document.querySelectorAll("header nav a[href]").forEach(function (a) {
      const url = new URL(a.href, window.location.href);
      if (url.pathname !== window.location.pathname) return;
      const id = url.hash
        ? url.hash.slice(1)
        : (a.hasAttribute("data-ir-arriba") ? "inicio" : "");
      if (id) enlaces.push({ a: a, id: id });
    });

    const secciones = document.querySelectorAll("section[id]");
    if (!enlaces.length || !secciones.length || !("IntersectionObserver" in window)) return;

    function marcar(idActivo) {
      enlaces.forEach(function (e) {
        if (e.id === idActivo) e.a.setAttribute("aria-current", "true");
        else e.a.removeAttribute("aria-current");
      });
      // "Nosotros" se marca cuando se ve alguna de sus secciones
      document.querySelectorAll("#menu-escritorio details").forEach(function (d) {
        d.toggleAttribute("data-activo", !!d.querySelector('a[aria-current="true"]'));
      });
    }

    const observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (entrada) {
        if (entrada.isIntersecting) marcar(entrada.target.id);
      });
    }, { rootMargin: "-35% 0px -60% 0px" });

    secciones.forEach(function (seccion) { observador.observe(seccion); });

    // En la portada, "La casa" queda marcada
    function revisarInicio() {
      if (window.scrollY < 120) marcar("inicio");
    }
    window.addEventListener("scroll", revisarInicio, { passive: true });
    revisarInicio();
  })();
})();
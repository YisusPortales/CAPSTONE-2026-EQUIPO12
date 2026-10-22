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
})();

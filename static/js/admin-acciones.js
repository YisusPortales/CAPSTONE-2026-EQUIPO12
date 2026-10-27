(function () {
  function iniciar() {
    var select = document.querySelector("#changelist-form select[name=action]");
    var ejecutar = document.querySelector("#changelist-form button[name=index]");
    var contenedor = document.querySelector("#changelist-form .actions");
    if (!select || !ejecutar || !contenedor) return;

    var barra = document.createElement("div");
    barra.className = "barra-acciones";
    barra.hidden = true;
    barra.setAttribute("role", "toolbar");

    var texto = document.createElement("span");
    texto.className = "barra-acciones-texto";
    barra.appendChild(texto);

    Array.prototype.forEach.call(select.options, function (op) {
      if (!op.value) return;
      var boton = document.createElement("button");
      boton.type = "button";
      var peligro = /delete|elimin|borrar/i.test(op.value + " " + op.text);
      boton.className = "barra-acciones-boton" + (peligro ? " peligro" : "");
      boton.textContent = op.text;
      boton.addEventListener("click", function () {
        select.value = op.value;
        ejecutar.click();
      });
      barra.appendChild(boton);
    });
    document.body.appendChild(barra);
    contenedor.classList.add("actions-ocultas");

    function actualizar() {
      var n = document.querySelectorAll("#changelist-form input.action-select:checked").length;
      barra.hidden = n === 0;
      texto.textContent = n + (n === 1 ? " seleccionado" : " seleccionados");
    }
    document.addEventListener("change", function (ev) {
      if (ev.target.matches("input.action-select, #action-toggle")) actualizar();
    });
    actualizar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();

// Pide confirmación antes de Aceptar / Rechazar una solicitud desde la fila.
document.addEventListener("click", function (ev) {
  var boton = ev.target.closest("[data-confirmar]");
  if (boton && !window.confirm(boton.dataset.confirmar)) {
    ev.preventDefault();
  }
}, true);
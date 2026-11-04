(function () {
  var caja = document.getElementById("espera-resena");
  if (!caja) return;
  var reloj = caja.querySelector("[data-reloj]");
  var boton = document.getElementById("enviar-resena");
  var restante = parseInt(caja.dataset.segundos, 10) || 0;
  var fin = Date.now() + restante * 1000;
  var id;

  function dos(n) { return (n < 10 ? "0" : "") + n; }

  function bloquear(si) {
    if (!boton) return;
    boton.disabled = si;
    boton.style.opacity = si ? ".5" : "";
    boton.style.cursor = si ? "not-allowed" : "";
  }

  function actualizar() {
    var s = Math.max(0, Math.ceil((fin - Date.now()) / 1000));
    reloj.textContent = dos(Math.floor(s / 60)) + ":" + dos(s % 60);
    if (s <= 0) {
      clearInterval(id);
      caja.hidden = true;
      bloquear(false);
    }
  }

  bloquear(true);
  actualizar();
  id = setInterval(actualizar, 1000);
})();
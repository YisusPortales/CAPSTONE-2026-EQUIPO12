(function () {
  var CLAVE = "theme"; // la misma clave que usa Django, así no se pisan

  function guardado() {
    try { return localStorage.getItem(CLAVE); } catch (e) { return null; }
  }

  function aplicar(modo) {
    document.documentElement.dataset.theme = modo;
    try { localStorage.setItem(CLAVE, modo); } catch (e) {}
  }

  // Predeterminado: oscuro. Solo queda en claro si el usuario lo eligió.
  aplicar(guardado() === "light" ? "light" : "dark");

  // Intercepta el botón antes de que Django haga su ciclo de 3 estados.
  document.addEventListener("click", function (ev) {
    if (!ev.target.closest(".theme-toggle")) return;
    ev.stopImmediatePropagation();
    aplicar(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  }, true);
})();
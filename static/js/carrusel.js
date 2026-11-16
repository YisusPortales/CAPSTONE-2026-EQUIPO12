(function () {
  "use strict";
  var reducir = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mostrar(boton, visible) {
    boton.classList.toggle("opacity-0", !visible);
    boton.classList.toggle("pointer-events-none", !visible);
    boton.tabIndex = visible ? 0 : -1;
    boton.setAttribute("aria-hidden", visible ? "false" : "true");
  }

  function iniciar(caja) {
    var pista = caja.querySelector("[data-pista]");
    var ant = caja.querySelector('[data-ir="-1"]');
    var sig = caja.querySelector('[data-ir="1"]');
    if (!pista || !ant || !sig) return;

    function actualizar() {
      var max = pista.scrollWidth - pista.clientWidth;
      var hay = max > 4;
      mostrar(ant, hay && pista.scrollLeft > 4);
      mostrar(sig, hay && pista.scrollLeft < max - 4);
    }
    function ir(dir) {
      pista.scrollBy({ left: dir * pista.clientWidth * 0.8, behavior: reducir ? "auto" : "smooth" });
    }

    ant.addEventListener("click", function () { ir(-1); });
    sig.addEventListener("click", function () { ir(1); });
    pista.addEventListener("scroll", actualizar, { passive: true });
    window.addEventListener("resize", actualizar);
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(actualizar);
      ro.observe(pista);
      Array.prototype.forEach.call(pista.children, function (hijo) { ro.observe(hijo); });
    }
    actualizar();
  }

  document.querySelectorAll("[data-carrusel]").forEach(iniciar);
})();
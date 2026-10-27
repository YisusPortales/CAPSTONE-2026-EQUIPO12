(function () {
  const raiz = document.documentElement;

  // Se aplica antes de pintar la página, para que no parpadee en claro.
  try {
    if (localStorage.getItem("tema") === "dark") raiz.dataset.tema = "dark";
  } catch (e) {}

  document.addEventListener("DOMContentLoaded", function () {
    const boton = document.getElementById("tema-toggle");
    if (!boton) return;

    function marcar() {
      boton.setAttribute("aria-pressed", raiz.dataset.tema === "dark" ? "true" : "false");
    }
    marcar();

    boton.addEventListener("click", function () {
      const oscuro = raiz.dataset.tema !== "dark";
      if (oscuro) raiz.dataset.tema = "dark";
      else delete raiz.dataset.tema;
      try { localStorage.setItem("tema", oscuro ? "dark" : "light"); } catch (e) {}
      marcar();
    });
  });
})();
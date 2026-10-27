(function () {
  // ---- Visor de fotos ----
  const visor = document.getElementById("visor");
  if (visor) {
    const img = visor.querySelector("img");
    document.querySelectorAll("[data-foto]").forEach(function (boton) {
      boton.addEventListener("click", function () {
        img.src = boton.dataset.foto;
        img.alt = boton.dataset.alt || "";
        visor.showModal();
      });
    });
    visor.addEventListener("click", function (e) {
      if (e.target === visor || e.target.closest("[data-cerrar]")) visor.close();
    });
    visor.addEventListener("close", function () { img.removeAttribute("src"); });
  }

  // ---- Filtros por categoría ----
  const filtros = document.querySelectorAll("[data-filtro]");
  const items = document.querySelectorAll("[data-item]");
  filtros.forEach(function (boton) {
    boton.addEventListener("click", function () {
      const f = boton.dataset.filtro;
      filtros.forEach(function (b) {
        b.setAttribute("aria-pressed", b === boton ? "true" : "false");
      });
      items.forEach(function (item) {
        item.hidden = !(f === "todas" || item.dataset.categoria === f);
      });
    });
  });

  // ---- Videos incrustados: no se carga nada de terceros hasta pulsar ----
  document.querySelectorAll("[data-embed]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      const marco = document.createElement("div");
      marco.className = boton.dataset.marco || "aspect-video";
      const iframe = document.createElement("iframe");
      iframe.src = boton.dataset.embed;
      iframe.title = boton.dataset.titulo || "";
      iframe.className = "h-full w-full border-0";
      iframe.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      iframe.allowFullscreen = true;
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      marco.appendChild(iframe);
      boton.replaceWith(marco);
    });
  });
})();
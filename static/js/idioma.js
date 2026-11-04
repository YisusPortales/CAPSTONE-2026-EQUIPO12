(function () {
  var raiz = document.documentElement;

  // Al cargar: si venimos de un cambio de idioma, se anima la entrada.
  try {
    if (sessionStorage.getItem("cambio-idioma") === "1") {
      sessionStorage.removeItem("cambio-idioma");
      raiz.classList.add("cambio-idioma");
    }
  } catch (e) {}

  // Al elegir un idioma: se atenúa la página y luego se envía el formulario.
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("#form-idioma button[name='language']");
    if (!boton) return;
    if (raiz.classList.contains("saliendo")) { e.preventDefault(); return; }
    if (boton.getAttribute("aria-current") === "true") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    e.preventDefault();
    try { sessionStorage.setItem("cambio-idioma", "1"); } catch (err) {}
    raiz.classList.add("saliendo");
    var form = boton.form;
    setTimeout(function () { form.requestSubmit(boton); }, 180);
  });
})();
(function () {
  if (!("IntersectionObserver" in window)) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  function yaVisible(el) {
    return el.getBoundingClientRect().top < window.innerHeight * 0.9;
  }

  function preparar(el, retraso) {
    // Lo que ya se ve al cargar la página no se anima.
    if (yaVisible(el)) return null;
    el.classList.add("reveal");
    if (retraso) el.style.setProperty("--reveal-delay", retraso + "ms");
    return el;
  }

  // Envuelve cada palabra de un título para animarla por separado.
  function dividirPalabras(titulo) {
    var indice = 0;

    function recorrer(nodo) {
      Array.prototype.slice.call(nodo.childNodes).forEach(function (hijo) {
        if (hijo.nodeType === 3) {
          var fragmento = document.createDocumentFragment();
          hijo.textContent.split(/(\s+)/).forEach(function (parte) {
            if (!parte) return;
            if (/^\s+$/.test(parte)) {
              fragmento.appendChild(document.createTextNode(" "));
              return;
            }
            var exterior = document.createElement("span");
            exterior.className = "palabra";
            exterior.setAttribute("aria-hidden", "true");
            var interior = document.createElement("span");
            interior.textContent = parte;
            interior.style.setProperty("--i", indice++);
            exterior.appendChild(interior);
            fragmento.appendChild(exterior);
          });
          nodo.replaceChild(fragmento, hijo);
        } else if (hijo.nodeType === 1 && hijo.tagName !== "BR") {
          recorrer(hijo);
        }
      });
    }

    // Los lectores de pantalla leen el título completo, no palabra por palabra.
    titulo.setAttribute("aria-label", titulo.textContent.trim().replace(/\s+/g, " "));
    recorrer(titulo);
    titulo.classList.add("titulo-animado");
  }

  function iniciar() {
    var objetivos = [];

    // 1) Elementos marcados a mano: <div data-reveal="left" data-reveal-delay="150">
    document.querySelectorAll("[data-reveal]").forEach(function (el) {
      var listo = preparar(el, parseInt(el.dataset.revealDelay || "0", 10));
      if (listo) objetivos.push(listo);
    });

    // 2) Automático: los bloques directos de cada <section>
    document.querySelectorAll("section").forEach(function (seccion) {
      if (seccion.closest("header, footer, nav")) return;
      if (seccion.hasAttribute("data-sin-animacion")) return;
      Array.prototype.forEach.call(seccion.children, function (hijo) {
        if (hijo.hasAttribute("data-reveal")) return;
        var listo = preparar(hijo, 0);
        if (listo) objetivos.push(listo);
      });
    });

    // 3) Grupos escalonados: <div data-reveal-grupo> anima sus hijos uno tras otro
    document.querySelectorAll("[data-reveal-grupo]").forEach(function (grupo) {
      Array.prototype.forEach.call(grupo.children, function (hijo, i) {
        var listo = preparar(hijo, i * 120);
        if (listo) objetivos.push(listo);
      });
    });

    // 4) Títulos: palabra por palabra
    document.querySelectorAll("section h1, section h2, section h3").forEach(function (titulo) {
      if (titulo.closest("header, footer, nav, [data-sin-animacion]")) return;
      if (titulo.classList.contains("titulo-animado")) return;
      if (yaVisible(titulo)) return;
      dividirPalabras(titulo);
      objetivos.push(titulo);
    });

    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (entrada) {
        if (entrada.isIntersecting) {
          entrada.target.classList.add("is-visible");
          observador.unobserve(entrada.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -8% 0px" });

    objetivos.forEach(function (el) { observador.observe(el); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
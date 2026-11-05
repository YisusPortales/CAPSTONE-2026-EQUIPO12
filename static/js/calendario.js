(function () {
  "use strict";
  var raiz = document.getElementById("rango-fechas");
  var inLlegada = document.getElementById("id_fecha_llegada");
  var inSalida = document.getElementById("id_fecha_salida");
  if (!raiz || !inLlegada || !inSalida) return;

  var T = raiz.dataset;
  var lang = document.documentElement.lang || "es";
  var form = inLlegada.form;
  var campos = document.getElementById("campos-fechas");
  var errores = document.getElementById("errores-fechas");
  var hoy = T.hoy;
  var ocupadas = {};            // noches ocupadas: "AAAA-MM-DD" -> true
  var llegada = inLlegada.value || "";
  var salida = inSalida.value || "";
  var limite = null;            // último día en que se puede salir, si ya hay llegada
  var hover = "";               // día bajo el mouse (vista previa del rango)
  var aviso = "";
  var abierto = false;
  var meses = 0;
  var vista = primerDia(llegada || hoy);
  var celdas = [];

  var fmtMes = new Intl.DateTimeFormat(lang, { month: "long", year: "numeric" });
  var fmtCorto = new Intl.DateTimeFormat(lang, { weekday: "short", day: "numeric", month: "short" });
  var fmtDia = new Intl.DateTimeFormat(lang, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  var fmtLargo = new Intl.DateTimeFormat(lang, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  var fmtSem = new Intl.DateTimeFormat(lang, { weekday: "short" });

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function parse(s) { var p = s.split("-"); return new Date(+p[0], +p[1] - 1, +p[2], 12); }
  function iso(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function suma(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function primerDia(s) { var d = parse(s); return new Date(d.getFullYear(), d.getMonth(), 1, 12); }
  function nochesEntre(a, b) { return Math.round((parse(b) - parse(a)) / 86400000); }
  function el(tag, cls, texto) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto !== undefined) e.textContent = texto;
    return e;
  }

  // Primera noche ocupada desde "desde": ese día ya se puede salir, pero no pasar de él.
  function limiteSalida(desde) {
    var d = parse(desde);
    for (var i = 0; i < 800; i++) {
      var k = iso(d);
      if (ocupadas[k]) return k;
      d = suma(d, 1);
    }
    return null;
  }

  // ---------- Estructura fija ----------
  var SVG_CAL = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="1.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>';
  var SVG_FLECHA = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 12h16M14 6l6 6-6 6"/></svg>';
  var SVG_CHEVRON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';

  function seg(etiqueta) {
    var s = el("span", "cal-seg");
    s.appendChild(el("small", null, etiqueta));
    s.valor = el("strong", null, "—");
    s.appendChild(s.valor);
    return s;
  }
  function icono(svg, cls) { var s = el("span", cls); s.innerHTML = svg; return s; }

  var envuelto = el("div", "cal-envuelto");
  var campo = el("button", "cal-campo");
  campo.type = "button";
  campo.setAttribute("aria-haspopup", "dialog");
  campo.setAttribute("aria-expanded", "false");
  var segLleg = seg(T.txtLlegada);
  var segSal = seg(T.txtSalida);
  campo.appendChild(icono(SVG_CAL, "cal-icono"));
  campo.appendChild(segLleg);
  campo.appendChild(icono(SVG_FLECHA, "cal-flecha"));
  campo.appendChild(segSal);
  campo.appendChild(icono(SVG_CHEVRON, "cal-chevron"));

  var pop = el("div", "cal-pop");
  pop.hidden = true;
  pop.setAttribute("role", "dialog");
  pop.setAttribute("aria-label", T.txtLlegada + " / " + T.txtSalida);
  var contMeses = el("div", "cal-meses");
  var pie = el("div", "cal-pie");
  var leyenda = el("span", "cal-leyenda");
  leyenda.appendChild(el("i"));
  leyenda.appendChild(el("span", null, T.txtNo));
  var vivo = el("span", "cal-vivo");
  pie.appendChild(leyenda);
  pie.appendChild(vivo);
  pop.appendChild(contMeses);
  pop.appendChild(pie);

  envuelto.appendChild(campo);
  envuelto.appendChild(pop);
  var contResumen = el("div");
  contResumen.setAttribute("aria-live", "polite");
  var titulo = el("h3", "cal-titulo-campo", T.txtElegirLlegada);
  raiz.appendChild(titulo);
  raiz.appendChild(envuelto);
  raiz.appendChild(contResumen);

  // Los campos reales siguen en el formulario (el servidor valida igual), pero ocultos.
  inLlegada.required = false;
  inSalida.required = false;
  if (campos) campos.style.display = "none";
  if (errores && errores.textContent.trim()) errores.style.display = "";

  // ---------- Abrir / cerrar ----------
  function abrir() {
    abierto = true;
    pop.hidden = false;
    raiz.classList.add("abierto");
    campo.setAttribute("aria-expanded", "true");
    pop.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  function cerrar(devolverFoco) {
    abierto = false;
    pop.hidden = true;
    hover = "";
    raiz.classList.remove("abierto");
    campo.setAttribute("aria-expanded", "false");
    if (devolverFoco) campo.focus();
  }
  campo.addEventListener("click", function () { abierto ? cerrar(false) : abrir(); });
  document.addEventListener("click", function (e) {
    // composedPath: sigue valiendo aunque el elemento pulsado se haya reemplazado al redibujar
    if (abierto && e.composedPath().indexOf(raiz) === -1) cerrar(false);
  });
  document.addEventListener("keydown", function (e) {
    if (abierto && e.key === "Escape") cerrar(true);
  });

  // ---------- Dibujo ----------
  function nav(dir) {
    var b = el("button", "cal-nav " + (dir < 0 ? "cal-prev" : "cal-next"), dir < 0 ? "‹" : "›");
    b.type = "button";
    b.setAttribute("aria-label", dir < 0 ? T.txtAnterior : T.txtSiguiente);
    if (dir < 0 && vista <= primerDia(hoy)) b.disabled = true;
    b.addEventListener("click", function () {
      vista = new Date(vista.getFullYear(), vista.getMonth() + dir, 1, 12);
      render();
      var nuevo = contMeses.querySelector(dir < 0 ? ".cal-prev" : ".cal-next");
      if (nuevo && !nuevo.disabled) nuevo.focus();
    });
    return b;
  }

  function mes(d, primero, ultimo) {
    var caja = el("div", "cal-mes");
    var cab = el("div", "cal-cab");
    cab.appendChild(primero ? nav(-1) : el("span"));
    cab.appendChild(el("span", "cal-titulo", fmtMes.format(d)));
    cab.appendChild(ultimo ? nav(1) : el("span"));
    caja.appendChild(cab);

    var sem = el("div", "cal-sem");
    for (var s = 0; s < 7; s++) sem.appendChild(el("span", null, fmtSem.format(new Date(2024, 0, 1 + s, 12))));
    caja.appendChild(sem);

    var dias = el("div", "cal-dias");
    var vacios = (new Date(d.getFullYear(), d.getMonth(), 1, 12).getDay() + 6) % 7; // semana desde lunes
    for (var v = 0; v < vacios; v++) dias.appendChild(el("span", "cal-vacio"));
    var total = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
    for (var n = 1; n <= total; n++) {
      var f = new Date(d.getFullYear(), d.getMonth(), n, 12);
      var k = iso(f);
      var b = el("button", "cal-dia", String(n));
      b.type = "button";
      b.dataset.k = k;
      celdas.push({ b: b, k: k, txt: fmtLargo.format(f) });
      dias.appendChild(b);
    }
    caja.appendChild(dias);
    return caja;
  }

  function estadoDe(k, previa) {
    var c = [];
    var off = false;
    if (k < hoy) {
      c.push("pasado"); off = true;
    } else if (k === llegada) {
      c.push("extremo");
      if (salida || previa) c.push("ini");
    } else if (k === salida) {
      c.push("extremo", "fin");
    } else if (llegada && !salida && k > llegada) {
      if (limite !== null && k > limite) { c.push(ocupadas[k] ? "ocupado" : "lejos"); off = true; }
      else if (previa && k === previa) c.push("extremo", "fin", "previa");
      else if (previa && k < previa) c.push("rango", "previa");
    } else if (ocupadas[k]) {
      c.push("ocupado"); off = true;
    } else if (llegada && salida && k > llegada && k < salida) {
      c.push("rango");
    }
    return { c: c, off: off };
  }

  // Actualiza solo las clases de los días (no recrea nada: el mouse no pierde el elemento).
  function pintar() {
    var previa = llegada && !salida && hover && hover > llegada ? hover : "";
    celdas.forEach(function (x) {
      var e = estadoDe(x.k, previa);
      x.b.className = "cal-dia " + e.c.join(" ");
      x.b.disabled = e.off;
      x.b.setAttribute("aria-label", x.txt + (e.off && x.k >= hoy ? ", " + T.txtNo : ""));
      if (x.k === llegada || x.k === salida) x.b.setAttribute("aria-pressed", "true");
      else x.b.removeAttribute("aria-pressed");
    });
    vivo.textContent = previa ? T.txtNoches + ": " + nochesEntre(llegada, previa) : "";
  }

  function setHover(k) {
    if (k !== hover) { hover = k; pintar(); }
  }

  contMeses.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".cal-dia") : null;
    if (b && !b.disabled) elegir(b.dataset.k);
  });
  function sobre(e) {
    var b = e.target.closest ? e.target.closest(".cal-dia") : null;
    if (b && !b.disabled && llegada && !salida) setHover(b.dataset.k);
  }
  function fuera(e) {
    var a = e.relatedTarget && e.relatedTarget.closest ? e.relatedTarget.closest(".cal-dia") : null;
    if (!a || a.disabled) setHover("");
  }
  contMeses.addEventListener("mouseover", sobre);
  contMeses.addEventListener("mouseout", fuera);
  contMeses.addEventListener("focusin", sobre);
  contMeses.addEventListener("focusout", fuera);

  function dato(etiqueta, valor) {
    var c = el("div", "cal-dato");
    c.appendChild(el("small", null, etiqueta));
    c.appendChild(el("strong", null, valor));
    return c;
  }

  function actualizarCampo() {
    segLleg.valor.textContent = llegada ? fmtCorto.format(parse(llegada)) : "—";
    segSal.valor.textContent = salida ? fmtCorto.format(parse(salida)) : "—";
    segLleg.classList.toggle("vacio", !llegada);
    segSal.classList.toggle("vacio", !salida);
  }

  function resumen() {
    contResumen.textContent = "";
    titulo.textContent = !llegada ? T.txtElegirLlegada : (!salida ? T.txtElegirSalida : T.txtLlegada + " → " + T.txtSalida);
    if (!llegada && !aviso) return;
    var caja = el("div", "cal-resumen");
    if (aviso) caja.appendChild(el("p", "cal-msg cal-error", aviso));
    if (llegada) {
      caja.appendChild(dato(T.txtLlegada, fmtDia.format(parse(llegada))));
      if (salida) {
        caja.appendChild(dato(T.txtSalida, fmtDia.format(parse(salida))));
        caja.appendChild(dato(T.txtNoches, String(nochesEntre(llegada, salida))));
      }
      var borrar = el("button", "cal-borrar", T.txtBorrar);
      borrar.type = "button";
      borrar.addEventListener("click", function () {
        llegada = ""; salida = ""; aviso = ""; hover = ""; limite = null;
        sincronizar(); pintar(); resumen(); actualizarCampo();
      });
      caja.appendChild(borrar);
    }
    contResumen.appendChild(caja);
  }

  function cuantosMeses() { return raiz.clientWidth >= 560 ? 2 : 1; }

  function render() {
    var n = cuantosMeses();
    meses = n;
    raiz.style.setProperty("--meses", n);
    raiz.dataset.meses = n;
    limite = llegada && !salida ? limiteSalida(llegada) : null;
    contMeses.textContent = "";
    celdas = [];
    for (var i = 0; i < n; i++) {
      var d = new Date(vista.getFullYear(), vista.getMonth() + i, 1, 12);
      contMeses.appendChild(mes(d, i === 0, i === n - 1));
    }
    pintar();
    resumen();
    actualizarCampo();
  }

  function sincronizar() {
    inLlegada.value = llegada;
    inSalida.value = salida;
    // htmx escucha "change" en estos campos y actualiza el aviso de disponibilidad.
    inLlegada.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function elegir(k) {
    aviso = "";
    var completo = false;
    if (llegada && !salida && k > llegada && (limite === null || k <= limite)) {
      salida = k;
      completo = true;
    } else {
      llegada = k;
      salida = "";
    }
    hover = "";
    limite = llegada && !salida ? limiteSalida(llegada) : null;
    sincronizar();
    pintar();
    resumen();
    actualizarCampo();
    if (completo) setTimeout(function () { cerrar(true); }, 220);
  }

  if (form) {
    form.addEventListener("submit", function (e) {
      if (!llegada || !salida) {
        e.preventDefault();
        aviso = T.txtFaltan;
        resumen();
        if (!abierto) abrir();
      }
    });
  }

  if ("ResizeObserver" in window) {
    new ResizeObserver(function () { if (cuantosMeses() !== meses) render(); }).observe(raiz);
  } else {
    window.addEventListener("resize", function () { if (cuantosMeses() !== meses) render(); });
  }
  render();

  fetch(T.url, { credentials: "same-origin", headers: { Accept: "application/json" } })
    .then(function (r) { return r.json(); })
    .then(function (datos) {
      datos.ocupadas.forEach(function (par) {
        var d = parse(par[0]);
        var fin = par[1];
        while (iso(d) < fin) { ocupadas[iso(d)] = true; d = suma(d, 1); }
      });
      render();
      if (llegada && salida) inLlegada.dispatchEvent(new Event("change", { bubbles: true }));
    })
    .catch(function () { /* sin la lista el calendario igual funciona; el servidor valida */ });
})();
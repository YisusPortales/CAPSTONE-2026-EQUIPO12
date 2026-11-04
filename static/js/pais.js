(function () {
  var cont = document.getElementById("selector-pais");
  if (!cont) return;
  var select = cont.querySelector("select");
  if (!select) return;

  var patron = cont.dataset.patron || "";
  var txt = {
    marcador: cont.dataset.marcador || "",
    vacio: cont.dataset.vacio || "",
    buscar: cont.dataset.buscar || "",
    sinResultados: cont.dataset.sinResultados || ""
  };

  function urlBandera(codigo) {
    return patron.replace("/xx.", "/" + codigo.toLowerCase() + ".");
  }
  function limpiar(s) {
    return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }
  function el(tag, estilo) {
    var e = document.createElement(tag);
    if (estilo) e.style.cssText = estilo;
    return e;
  }

  // Datos: salen del <select> que genera Django.
  var datos = Array.prototype.slice.call(select.options).map(function (o) {
    return { codigo: o.value, nombre: o.text, buscable: limpiar(o.text) };
  });
  if (!datos.length || datos[0].codigo !== "") {
    datos.unshift({ codigo: "", nombre: txt.vacio, buscable: "" });
  } else {
    datos[0].nombre = txt.vacio;
  }

  // El botón copia el aspecto del <select> original.
  var estilo = window.getComputedStyle(select);
  var boton = el("button", "display:flex;align-items:center;gap:.6rem;width:100%;text-align:left;cursor:pointer;");
  boton.type = "button";
  boton.setAttribute("aria-haspopup", "listbox");
  boton.setAttribute("aria-expanded", "false");
  boton.style.backgroundColor = estilo.backgroundColor;
  boton.style.color = estilo.color;
  boton.style.border = estilo.borderTopWidth + " " + estilo.borderTopStyle + " " + estilo.borderTopColor;
  boton.style.borderRadius = estilo.borderTopLeftRadius;
  boton.style.padding = estilo.paddingTop + " " + estilo.paddingRight + " " + estilo.paddingBottom + " " + estilo.paddingLeft;
  boton.style.fontSize = estilo.fontSize;
  boton.style.fontFamily = estilo.fontFamily;

  var cuerpo = el("span", "display:flex;align-items:center;gap:.6rem;flex:1;min-width:0;");
  var flecha = el("span", "display:inline-flex;flex-shrink:0;");
  flecha.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>';
  boton.appendChild(cuerpo);
  boton.appendChild(flecha);

  // Panel desplegable: buscador + lista.
  var panel = el("div", "position:absolute;left:0;right:0;top:calc(100% + .25rem);z-index:20;background:#16261f;color:#fff;border:1px solid rgba(255,255,255,.2);border-radius:.5rem;box-shadow:0 10px 30px rgba(0,0,0,.35);overflow:hidden;");
  panel.hidden = true;
  var buscador = el("input", "width:100%;box-sizing:border-box;background:transparent;color:#fff;border:0;border-bottom:1px solid rgba(255,255,255,.2);padding:.65rem .75rem;font:inherit;outline:none;");
  buscador.type = "search";
  buscador.placeholder = txt.buscar;
  buscador.setAttribute("aria-label", txt.buscar);
  buscador.setAttribute("autocomplete", "off");
  buscador.setAttribute("role", "combobox");
  buscador.setAttribute("aria-expanded", "true");
  var lista = el("ul", "max-height:16rem;overflow:auto;margin:0;padding:.25rem 0;list-style:none;");
  lista.setAttribute("role", "listbox");
  lista.id = "lista-paises";
  buscador.setAttribute("aria-controls", lista.id);
  var sinRes = el("li", "padding:.6rem .75rem;opacity:.7;");
  sinRes.textContent = txt.sinResultados;
  sinRes.hidden = true;
  panel.appendChild(buscador);
  panel.appendChild(lista);

  // Se oculta el <select>, pero sigue dentro del formulario y es el que se envía.
  select.setAttribute("aria-hidden", "true");
  select.tabIndex = -1;
  select.style.cssText = "position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;";
  cont.style.position = "relative";
  cont.appendChild(boton);
  cont.appendChild(panel);

  var items = [];
  var visibles = [];
  var activo = -1;

  function contenidoDe(dato, destino) {
    destino.textContent = "";
    if (dato.codigo) {
      var img = el("img", "width:1.4rem;height:auto;flex-shrink:0;border-radius:2px;");
      img.alt = "";
      img.loading = "lazy";
      img.src = urlBandera(dato.codigo);
      destino.appendChild(img);
    }
    var t = el("span", "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;");
    t.textContent = dato.nombre;
    destino.appendChild(t);
  }

  function datoActual() {
    for (var i = 0; i < datos.length; i++) {
      if (datos[i].codigo === select.value) return datos[i];
    }
    return datos[0];
  }

  function pintarBoton() {
    var d = datoActual();
    if (d.codigo) {
      contenidoDe(d, cuerpo);
    } else {
      cuerpo.textContent = "";
      var m = el("span", "opacity:.8;");
      m.textContent = txt.marcador;
      cuerpo.appendChild(m);
    }
  }

  function crearItems() {
    datos.forEach(function (d, i) {
      var li = el("li", "display:flex;align-items:center;gap:.6rem;padding:.45rem .75rem;cursor:pointer;");
      li.className = "pais-op";
      li.id = "pais-op-" + i;
      li.setAttribute("role", "option");
      li.dataset.i = i;
      contenidoDe(d, li);
      li.addEventListener("mousedown", function (e) { e.preventDefault(); });
      li.addEventListener("click", function () { elegir(i); });
      li.addEventListener("mousemove", function () { marcar(visibles.indexOf(li), false); });
      items.push(li);
      lista.appendChild(li);
    });
    lista.appendChild(sinRes);
  }

  function marcar(n, desplazar) {
    if (activo >= 0 && visibles[activo]) visibles[activo].classList.remove("activa");
    activo = n;
    if (n >= 0 && visibles[n]) {
      visibles[n].classList.add("activa");
      buscador.setAttribute("aria-activedescendant", visibles[n].id);
      if (desplazar) visibles[n].scrollIntoView({ block: "nearest" });
    } else {
      buscador.removeAttribute("aria-activedescendant");
    }
  }

  function filtrar() {
    var q = limpiar(buscador.value.trim());
    visibles = [];
    items.forEach(function (li, i) {
      var coincide = !q || datos[i].buscable.indexOf(q) !== -1;
      li.style.display = coincide ? "flex" : "none";
      if (coincide) visibles.push(li);
    });
    sinRes.hidden = visibles.length > 0;
    marcar(visibles.length ? 0 : -1, true);
  }

  function abrir() {
    if (!items.length) crearItems();
    panel.hidden = false;
    boton.setAttribute("aria-expanded", "true");
    buscador.value = "";
    filtrar();
    items.forEach(function (li, i) {
      li.setAttribute("aria-selected", datos[i].codigo === select.value ? "true" : "false");
    });
    var sel = items.filter(function (li, i) { return datos[i].codigo === select.value; })[0];
    if (sel && visibles.indexOf(sel) !== -1) marcar(visibles.indexOf(sel), true);
    buscador.focus();
  }

  function cerrar(devolverFoco) {
    if (panel.hidden) return;
    panel.hidden = true;
    boton.setAttribute("aria-expanded", "false");
    if (devolverFoco) boton.focus();
  }

  function elegir(i) {
    select.value = datos[i].codigo;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    pintarBoton();
    cerrar(true);
  }

  boton.addEventListener("click", function () { panel.hidden ? abrir() : cerrar(false); });
  boton.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); if (panel.hidden) abrir(); }
  });
  buscador.addEventListener("input", filtrar);
  buscador.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); if (visibles.length) marcar(Math.min(activo + 1, visibles.length - 1), true); }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (visibles.length) marcar(Math.max(activo - 1, 0), true); }
    else if (e.key === "Enter") { e.preventDefault(); if (activo >= 0 && visibles[activo]) elegir(+visibles[activo].dataset.i); }
    else if (e.key === "Escape") { e.preventDefault(); cerrar(true); }
    else if (e.key === "Tab") { cerrar(false); }
  });
  document.addEventListener("mousedown", function (e) {
    if (!cont.contains(e.target)) cerrar(false);
  });
  // Si se hace clic en la etiqueta del campo, el foco pasa al botón.
  select.addEventListener("focus", function () { boton.focus(); });

  pintarBoton();
})();
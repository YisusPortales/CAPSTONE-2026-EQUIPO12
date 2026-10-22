"""Compila las traducciones del sitio sin necesitar gettext.

Uso (desde la raiz del proyecto):

    python herramientas/compilar_traducciones.py

Hace dos cosas:
  1. Convierte cada locale/<idioma>/LC_MESSAGES/django.po en django.mo,
     que es el archivo que Django lee al mostrar el sitio.
  2. Avisa de los textos del codigo o de las plantillas que todavia no
     estan traducidos (por ejemplo, un texto nuevo que agregaste).

Despues de compilar, detén el servidor (Ctrl+C) y vuelve a iniciarlo.
"""

import ast
import array
import re
import struct
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXCLUIDAS = {".venv", "venv", "migrations", "herramientas", "locale", "wheels", "node_modules", "__pycache__"}


def desescapar(texto: str) -> str:
    return (
        texto.replace(r"\n", "\n").replace(r"\t", "\t").replace(r'\"', '"').replace("\\\\", "\\")
    )


def escapar(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace('"', r"\"").replace("\n", r"\n").replace("\t", r"\t")


def leer_po(ruta: Path) -> dict:
    """Lee un .po simple (msgid/msgstr, con lineas de continuacion)."""
    mensajes, actual, campo = {}, {"msgid": "", "msgstr": ""}, None
    fuzzy = False

    def cerrar():
        nonlocal actual, campo, fuzzy
        if actual["msgid"] is not None and (actual["msgstr"] or actual["msgid"] == "") and not fuzzy:
            mensajes[actual["msgid"]] = actual["msgstr"]
        actual, campo, fuzzy = {"msgid": None, "msgstr": ""}, None, False

    actual = {"msgid": None, "msgstr": ""}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea.startswith("#,") and "fuzzy" in linea:
            fuzzy = True
        elif linea.startswith("#") or not linea:
            if not linea and campo == "msgstr":
                cerrar()
        elif linea.startswith("msgid "):
            if campo == "msgstr":
                cerrar()
            actual["msgid"] = desescapar(linea[7:-1])
            campo = "msgid"
        elif linea.startswith("msgstr "):
            actual["msgstr"] = desescapar(linea[8:-1])
            campo = "msgstr"
        elif linea.startswith('"') and campo:
            actual[campo] = (actual[campo] or "") + desescapar(linea[1:-1])
    if campo == "msgstr":
        cerrar()
    return mensajes


def escribir_mo(mensajes: dict, destino: Path) -> None:
    datos = {k.encode("utf-8"): v.encode("utf-8") for k, v in mensajes.items()}
    claves = sorted(datos)
    desplazamientos, ids, cadenas = [], b"", b""
    for clave in claves:
        desplazamientos.append((len(ids), len(clave), len(cadenas), len(datos[clave])))
        ids += clave + b"\0"
        cadenas += datos[clave] + b"\0"
    inicio_claves = 7 * 4 + 16 * len(claves)
    inicio_valores = inicio_claves + len(ids)
    tabla_claves, tabla_valores = [], []
    for o1, l1, o2, l2 in desplazamientos:
        tabla_claves += [l1, o1 + inicio_claves]
        tabla_valores += [l2, o2 + inicio_valores]
    salida = struct.pack("Iiiiiii", 0x950412DE, 0, len(claves), 7 * 4, 7 * 4 + len(claves) * 8, 0, 0)
    salida += array.array("i", tabla_claves + tabla_valores).tobytes()
    salida += ids + cadenas
    destino.write_bytes(salida)


def textos_del_proyecto() -> set:
    encontrados = set()
    for ruta in RAIZ.rglob("*.py"):
        if EXCLUIDAS & set(ruta.relative_to(RAIZ).parts):
            continue
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                    and nodo.func.id in {"_", "gettext", "gettext_lazy"}
                    and nodo.args and isinstance(nodo.args[0], ast.Constant)
                    and isinstance(nodo.args[0].value, str)):
                encontrados.add(nodo.args[0].value)
    patrones = (
        re.compile(r"""\{%\s*(?:translate|trans)\s+(["'])(.*?)\1""", re.S),
        re.compile(r"""(?<![\w.])_\(\s*(["'])(.*?)\1\s*\)""", re.S),
    )
    for ruta in RAIZ.rglob("*.html"):
        if EXCLUIDAS & set(ruta.relative_to(RAIZ).parts):
            continue
        texto = ruta.read_text(encoding="utf-8")
        for patron in patrones:
            encontrados.update(m.group(2) for m in patron.finditer(texto))
    return encontrados


def main() -> int:
    archivos = sorted((RAIZ / "locale").glob("*/LC_MESSAGES/django.po"))
    if not archivos:
        print("No se encontraron archivos .po en la carpeta locale.")
        return 1
    en_codigo = textos_del_proyecto()
    hay_faltantes = False
    for po in archivos:
        idioma = po.parent.parent.name
        mensajes = leer_po(po)
        escribir_mo(mensajes, po.with_suffix(".mo"))
        print(f"OK  {idioma}: {len(mensajes) - 1} textos -> {po.with_suffix('.mo').relative_to(RAIZ)}")
        faltan = sorted(t for t in en_codigo if t not in mensajes)
        if faltan:
            hay_faltantes = True
            print(f"    AVISO: {len(faltan)} texto(s) sin traducir en '{idioma}':")
            for texto in faltan:
                print(f"      - {texto}")
    if not hay_faltantes:
        print("Todos los textos del sitio estan traducidos.")
    print("Ahora reinicia el servidor (Ctrl+C y python manage.py runserver).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

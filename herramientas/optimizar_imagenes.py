"""Convierte y reduce fotos para usarlas en el sitio.

Uso (desde la raiz del proyecto, con el entorno virtual activado):

    python -m pip install pillow
    python herramientas/optimizar_imagenes.py CARPETA_CON_FOTOS
    python herramientas/optimizar_imagenes.py CARPETA_CON_FOTOS --formato webp --ancho 1600

Cada foto se guarda en static/img con el nombre en minusculas y sin espacios
ni tildes. El archivo queda sin metadatos (EXIF), lo que elimina datos como la
ubicacion GPS donde se tomo la foto.
"""

import argparse
import re
import unicodedata
from pathlib import Path

from PIL import Image, ImageOps

EXTENSIONES = {".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def nombre_seguro(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")
    return limpio or "imagen"


def main():
    parser = argparse.ArgumentParser(description="Optimiza fotos para el sitio.")
    parser.add_argument("origen", type=Path, help="carpeta con las fotos originales")
    parser.add_argument("--destino", type=Path, default=Path("static/img"))
    parser.add_argument("--ancho", type=int, default=1920, help="ancho maximo en pixeles")
    parser.add_argument("--calidad", type=int, default=82, help="calidad de 1 a 100")
    parser.add_argument("--formato", choices=["jpg", "webp"], default="jpg")
    args = parser.parse_args()

    if not args.origen.is_dir():
        raise SystemExit(f"No existe la carpeta: {args.origen}")
    args.destino.mkdir(parents=True, exist_ok=True)

    procesadas = 0
    for archivo in sorted(args.origen.iterdir()):
        if archivo.suffix.lower() not in EXTENSIONES:
            continue
        with Image.open(archivo) as original:
            imagen = ImageOps.exif_transpose(original)  # respeta la orientacion
            if imagen.width > args.ancho:
                alto = round(imagen.height * args.ancho / imagen.width)
                imagen = imagen.resize((args.ancho, alto), Image.Resampling.LANCZOS)
            if imagen.mode in ("RGBA", "LA", "P"):
                fondo = Image.new("RGB", imagen.size, (255, 255, 255))
                imagen = imagen.convert("RGBA")
                fondo.paste(imagen, mask=imagen.getchannel("A"))
                imagen = fondo
            else:
                imagen = imagen.convert("RGB")
            salida = args.destino / f"{nombre_seguro(archivo.stem)}.{args.formato}"
            formato = "JPEG" if args.formato == "jpg" else "WEBP"
            # No se pasa el parametro exif: el archivo resultante no lleva metadatos.
            imagen.save(salida, formato, quality=args.calidad, optimize=True)
        print(f"{archivo.name} -> {salida} ({salida.stat().st_size // 1024} KB)")
        procesadas += 1

    print(f"Listo: {procesadas} imagen(es) en {args.destino}")


if __name__ == "__main__":
    main()

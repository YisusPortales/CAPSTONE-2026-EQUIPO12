"""Convierte cualquier video a MP4 (H.264) para que se vea en todos los navegadores.

Requiere ffmpeg instalado. En Windows, desde PowerShell:

    winget install Gyan.FFmpeg
    (cierra y vuelve a abrir la terminal)

Uso (desde la raiz del proyecto):

    python herramientas/optimizar_videos.py CARPETA_O_ARCHIVO
    python herramientas/optimizar_videos.py mi_video.mov --nombre presentacion

El resultado queda en static/video/ (por defecto con el nombre del original,
en minusculas y sin espacios ni tildes), sin metadatos, y se genera una
imagen de portada en static/img/NOMBRE.jpg para usarla como poster.
"""

import argparse
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

EXTENSIONES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv", ".3gp", ".mpg", ".mpeg"}


def nombre_seguro(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")
    return limpio or "video"


def convertir(origen: Path, destino_video: Path, destino_img: Path, nombre: str, alto: int, crf: int):
    salida = destino_video / f"{nombre}.mp4"
    comando = [
        "ffmpeg", "-y", "-i", str(origen),
        "-vf", f"scale=-2:'min({alto},ih)'",
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-map_metadata", "-1",
        "-movflags", "+faststart",
        str(salida),
    ]
    subprocess.run(comando, check=True)
    poster = destino_img / f"{nombre}.jpg"
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "1", "-i", str(salida), "-frames:v", "1", "-q:v", "3", str(poster)],
        check=True,
    )
    mb = salida.stat().st_size / 1_000_000
    print(f"OK  {origen.name} -> {salida} ({mb:.1f} MB) + {poster}")


def main():
    parser = argparse.ArgumentParser(description="Convierte videos a MP4 H.264.")
    parser.add_argument("origen", type=Path, help="video o carpeta con videos")
    parser.add_argument("--nombre", help="nombre de salida (solo si es un video)")
    parser.add_argument("--destino", type=Path, default=Path("static/video"))
    parser.add_argument("--destino-img", type=Path, default=Path("static/img"))
    parser.add_argument("--alto", type=int, default=1080, help="alto maximo en pixeles")
    parser.add_argument("--crf", type=int, default=26, help="calidad: menor = mejor y mas pesado")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("No se encontro ffmpeg. Instalalo con: winget install Gyan.FFmpeg (y reabre la terminal)")
    if not args.origen.exists():
        raise SystemExit(f"No existe: {args.origen}")

    if args.origen.is_dir():
        videos = sorted(p for p in args.origen.iterdir() if p.suffix.lower() in EXTENSIONES)
    else:
        videos = [args.origen]
    if not videos:
        raise SystemExit("No se encontraron videos.")

    args.destino.mkdir(parents=True, exist_ok=True)
    args.destino_img.mkdir(parents=True, exist_ok=True)
    for video in videos:
        nombre = nombre_seguro(args.nombre) if args.nombre and len(videos) == 1 else nombre_seguro(video.stem)
        convertir(video, args.destino, args.destino_img, nombre, args.alto, args.crf)


if __name__ == "__main__":
    main()

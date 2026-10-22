# Prepara y abre el proyecto en un computador nuevo (Windows, PowerShell).
#
# Uso (desde la carpeta del proyecto):
#   powershell -ExecutionPolicy Bypass -File .\iniciar_demo.ps1
#
# Requisitos: Python 3.12 o superior instalado (python.org) y, la primera vez,
# conexion a internet para instalar las dependencias (o una carpeta "wheels").
# Nota: el texto del script no usa tildes a proposito, para evitar problemas de
# codificacion en Windows PowerShell.

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Fallo($mensaje) {
    Write-Host ""
    Write-Host "ERROR: $mensaje" -ForegroundColor Red
    exit 1
}

# 1. Buscar una version de Python compatible (3.12 o superior)
$lanzador = $null   # "py" (con version) o "python"
$version = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in "3.13", "3.14", "3.12") {
        py "-$v" --version *> $null
        if ($LASTEXITCODE -eq 0) { $lanzador = "py"; $version = $v; break }
    }
}
if (-not $lanzador -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $texto = (python --version 2>&1) | Out-String
    if ($texto -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 12) {
        $lanzador = "python"
        $version = "3." + $Matches[1]
    }
}
if (-not $lanzador) {
    Fallo "No se encontro Python 3.12 o superior. Instalalo desde python.org (marca 'Add python.exe to PATH')."
}
Write-Host "Usando Python $version" -ForegroundColor Green

# 2. Crear el entorno virtual si no existe
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Creando entorno virtual..."
    if ($lanzador -eq "py") { py "-$version" -m venv .venv } else { python -m venv .venv }
    if ($LASTEXITCODE -ne 0) { Fallo "No se pudo crear el entorno virtual." }
}
. .\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias (sin internet si existe la carpeta "wheels")
Write-Host "Instalando dependencias..."
if (Test-Path "wheels") {
    python -m pip install --no-index --find-links wheels -r requirements.txt
} else {
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
}
if ($LASTEXITCODE -ne 0) { Fallo "No se pudieron instalar las dependencias." }

# 4. Crear el archivo .env con una clave nueva si no existe
if (-not (Test-Path ".env")) {
    Write-Host "Creando .env con una clave secreta nueva..."
    $clave = python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
    $lineas = @("DJANGO_SECRET_KEY='$clave'", "DJANGO_DEBUG=1")
    Set-Content -Path ".env" -Value $lineas -Encoding ascii
}

# 5. Verificar que exista el CSS compilado de Tailwind
if (-not (Test-Path "static\css\styles.css")) {
    Write-Host "Falta static\css\styles.css. Compilando con Tailwind (necesita internet)..." -ForegroundColor Yellow
    python -m pip install pytailwindcss
    tailwindcss -i static/css/input.css -o static/css/styles.css --minify
    if (-not (Test-Path "static\css\styles.css")) { Fallo "No se pudo generar el CSS." }
}

# 6. Base de datos y datos iniciales
python manage.py migrate
if ($LASTEXITCODE -ne 0) { Fallo "Fallaron las migraciones." }
python manage.py loaddata datos_iniciales
if ($LASTEXITCODE -ne 0) { Fallo "No se pudieron cargar los datos iniciales." }

# 7. Usuario administrador (opcional)
$respuesta = Read-Host "Crear usuario administrador para el panel /admin? (s/N)"
if ($respuesta -eq "s" -or $respuesta -eq "S") {
    python manage.py createsuperuser
}

# 8. Abrir el sitio y arrancar el servidor
Write-Host ""
Write-Host "Sitio:  http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Panel:  http://127.0.0.1:8000/admin/   (Ctrl+C para detener el servidor)" -ForegroundColor Green
Start-Process "http://127.0.0.1:8000/"
python manage.py runserver

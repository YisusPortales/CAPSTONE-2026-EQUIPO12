# Plataforma web para Hospedaje Rural Pirque

Proyecto APT (Capstone, PTY 4614) de Ingenieria en Informatica, Duoc UC, sede San Bernardo.

Plataforma web multilingue para Hospedaje Rural Pirque, un hospedaje rural boutique ubicado en Pirque, Region Metropolitana, Chile. Presenta su oferta (habitaciones, servicios, historia y ubicacion) y gestiona solicitudes de reserva con una base de datos propia, aplicando controles de seguridad y pruebas documentadas.

Estado: en desarrollo.

## Problema que resuelve

El hospedaje no tiene una pagina web funcional, por lo que tiene poca visibilidad ante el publico general y los turistas extranjeros, y tampoco cuenta con un canal ordenado para recibir solicitudes de reserva. Como el formulario maneja datos personales de los huespedes, la seguridad se considera desde el diseno.

## Tecnologias

- Backend y API: Python y Django (endpoints HTTP)
- Frontend: plantillas de Django, htmx y Tailwind CSS, con i18n
- Base de datos: SQLite, mediante el ORM de Django
- Correos: Twilio SendGrid (API)
- Despliegue: AWS EC2 con Nginx, Gunicorn y HTTPS

Flujo general: Usuario -> Frontend -> API -> Backend -> Base de datos

## Estado del desarrollo

Implementado:

- Modelo de datos: habitaciones, servicios, huespedes y solicitudes de reserva, con validaciones y restricciones de integridad
- Panel de administracion de Django para gestionar los datos
- Pruebas automatizadas de los modelos

Planificado:

- Sitio informativo en espanol, ingles y portugues, con soporte para idiomas adicionales
- Formulario de solicitud de reserva con validacion en el servidor
- Correos de confirmacion y aviso con SendGrid
- Inicio de sesion seguro, roles y gestion de solicitudes
- Revision de seguridad segun OWASP Top 10
- Despliegue en AWS EC2 con HTTPS

## Requisitos

- Python 3.12 o superior (probado con Python 3.13)
- Git

## Instalacion (Windows, PowerShell)

Clonar el repositorio y crear el entorno virtual:

    git clone https://github.com/YisusPortales/CAPSTONE-2026-EQUIPO12/tree/main
    cd ProyectoHospedaje
    py -3.13 -m venv .venv
    .venv\Scripts\activate

Instalar las dependencias:

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

En macOS o Linux, el entorno se activa con: source .venv/bin/activate

## Variables de entorno

La configuracion sensible no esta en el codigo. Los nombres de las variables estan en el archivo .env.example. Hay que definirlas en la terminal antes de ejecutar:

    $env:DJANGO_SECRET_KEY = 'una-clave-secreta-larga-y-aleatoria'
    $env:DJANGO_DEBUG = "1"

Para generar una clave aleatoria:

    python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"

DJANGO_DEBUG igual a 1 solo debe usarse en desarrollo. DJANGO_ALLOWED_HOSTS es opcional (por defecto localhost y 127.0.0.1).

## Ejecutar

    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

El panel de administracion queda en http://127.0.0.1:8000/admin

## Pruebas

    python manage.py test

## Estructura

- config: configuracion del proyecto Django
- reservas: aplicacion principal con modelos, administracion y pruebas
- manage.py: utilidad de linea de comandos de Django

## Seguridad

- La clave secreta y el modo de depuracion se leen de variables de entorno y no se suben al repositorio.
- Las validaciones se aplican en el servidor y tambien como restricciones de la base de datos.
- Los datos de prueba son ficticios. No se suben datos reales de huespedes.
- Esta previsto revisar el sistema segun OWASP Top 10 antes de la entrega.

## Metodologia

El proyecto se desarrolla con Scrum, adaptado a trabajo individual: sprints semanales, product backlog con historias de usuario, scrumboard, definicion de hecho (con pruebas y revision de seguridad), review y retrospectiva.

## Autor

Jesus Portales Gajardo, Ingenieria en Informatica, Duoc UC.
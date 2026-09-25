# Cumbre Digital MX 2026 — Proyecto de Práctica

## Sobre este proyecto
App web de registro de asistentes para "Cumbre Digital MX 2026".

## Stack tecnológico
- Fase 1: HTML + CSS + JavaScript (sin servidor)
- Fase 2: Python 3 + Flask + SQLite
- Despliegue: Render.com (opcional)

## Reglas de trabajo
- Todo el contenido y comentarios en español
- Sin frameworks CSS externos (solo CSS puro)
- Diseño responsivo, tema oscuro, moderno
- La base de datos se llama evento.db y está en la raíz del proyecto
- Sin autenticación ni login de momento
- Mensajes de error claros en español

## Estructura del proyecto (Fase 2)
- app.py → servidor Flask principal
- evento.db → base de datos SQLite (tabla `asistentes`; se crea sola al arrancar, no se sube a git)
- templates/ → páginas HTML (base, index, confirmacion, admin, error)
- static/estilos.css → CSS compartido por todas las páginas
- fase1/index.html → versión estática original (respaldo)
- requirements.txt → dependencias Python
- Procfile → configuración para Render
- venv/ → ambiente virtual (no se sube a git)

## Cómo ejecutar en local (PowerShell)
- Usar `py` (el comando `python` es solo el alias de la Microsoft Store)
- Crear venv: `py -m venv venv` · Activar: `.\venv\Scripts\Activate.ps1`
- Instalar: `pip install -r requirements.txt` · Correr: `python app.py` → http://127.0.0.1:5000
- Panel de asistentes: http://127.0.0.1:5000/admin

## Contexto del evento
- Nombre: Cumbre Digital MX 2026
- Tema: Transformación digital para PyMEs
- Campos del formulario: nombre completo, email, empresa, área de interés
- Áreas: Tecnología / Marketing / Negocios / Emprendimiento

## Servidores MCP disponibles (alcance proyecto)
- github: para subir el código al repositorio
- sqlite: para interactuar con evento.db (se agrega en Fase 2)
- playwright: para pruebas automáticas (Fase 3)